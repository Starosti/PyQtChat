"""
Chat tab widget representing a single chat session.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QInputDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from ui.chat_message import ChatMessage
from core.chat_worker import ChatWorker
from core.settings import settings_manager
from utils.cost_tracker import (
    calculate_message_cost,
    estimate_tokens,
)
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextOption


class ChatTab(QWidget):
    """Widget representing a single chat session with its own history."""

    # Signals
    message_sent = pyqtSignal(str, int)  # Message, tab index
    status_changed = pyqtSignal(str, int)  # Status message, tab index
    cost_updated = pyqtSignal(float)  # Total cost (for parent to display)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.conversation_history: List[Dict] = []
        self.current_ai_message = ""
        self.chat_worker = None
        self.current_model = None
        self.ai_message_widget = None
        self.tab_index = -1  # Will be set when added to parent

        # Cost tracking
        self.total_cost = 0.0
        self.current_message_cost = 0.0
        self.cost_tracking_enabled = True

        # Default suggestions for empty chat
        self.default_suggestions = [
            "Hello!",
            "Tell me a joke",
            "Explain quantum computing",
            'Give me "Hello, World!" in 5 different programming languages',
        ]

        self.setup_ui()

    def setup_ui(self):
        """Set up the chat tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # Apply initial font from parent if available
        if self.parent and hasattr(self.parent, "font"):
            self.setFont(self.parent.font())

        # Chat display area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.chat_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Container widget for messages
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)

        # Add suggestions widget when chat is empty
        self.create_suggestions_widget()
        self.chat_layout.addWidget(self.suggestions_widget)

        self.chat_layout.addStretch()  # Push messages to top
        self.chat_container.setLayout(self.chat_layout)
        self.chat_scroll.setWidget(self.chat_container)

        layout.addWidget(self.chat_scroll)

        # Input area
        input_layout = QHBoxLayout()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        if self.parent and hasattr(self.parent, "font"):  # Apply font during setup
            self.message_input.setFont(self.parent.font())

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setDefault(True)
        if self.parent and hasattr(self.parent, "font"):  # Apply font during setup
            self.send_button.setFont(self.parent.font())

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

    def create_suggestions_widget(self):
        """Create suggestion buttons widget."""
        self.suggestions_widget = QWidget()
        layout = QVBoxLayout(self.suggestions_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel("Try one of these:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.parent and hasattr(self.parent, "font"):  # Apply font during setup
            label.setFont(self.parent.font())
            self.suggestions_widget.setFont(self.parent.font())
        layout.addWidget(label)

        for suggestion in self.default_suggestions:
            btn = QPushButton(suggestion)
            if self.parent and hasattr(self.parent, "font"):  # Apply font during setup
                btn.setFont(self.parent.font())
            btn.clicked.connect(lambda _, s=suggestion: self.handle_suggestion_click(s))
            layout.addWidget(btn)
        self.suggestions_widget.setLayout(layout)

    def handle_suggestion_click(self, text):
        """Handle suggestion button click."""
        self.message_input.setText(text)
        self.send_message()

    def set_tab_index(self, index):
        """Set the index of this tab in the parent's tab list."""
        self.tab_index = index

    def set_model(self, model):
        """Set the model to use for this chat."""
        self.current_model = model

    def set_current_model_cost_info(self, model):
        """Update the cost info for the current model."""
        # No UI updates needed here, just tracking the model
        self.current_model = model

    def get_status(self):
        """Get the current status of this chat."""
        if self.chat_worker and self.chat_worker.isRunning():
            return "Receiving message..."
        return "Ready"

    def terminate_worker(self):
        """Safely terminate the chat worker thread if it's running."""
        if self.chat_worker and self.chat_worker.isRunning():
            logging.info(f"Terminating worker in tab {self.tab_index}")
            try:
                self.chat_worker.stop_safely()
            except Exception as e:
                logging.error(f"Error stopping worker in tab {self.tab_index}: {e}")
                # Force terminate if stop_safely fails
                if self.chat_worker.isRunning():
                    self.chat_worker.terminate()
                    self.chat_worker.wait()
            finally:
                self.chat_worker = None

    def send_message(self):
        """Send a message to the AI."""
        # First, terminate any existing worker
        self.terminate_worker()

        # Hide suggestions on first user message
        if hasattr(self, "suggestions_widget") and self.suggestions_widget.isVisible():
            self.suggestions_widget.hide()

        message = self.message_input.text().strip()
        if not message:
            return

        # Double-check if a worker is already running after termination
        if self.chat_worker is not None and self.chat_worker.isRunning():
            QMessageBox.warning(
                self,
                "Processing",
                "An AI response is already being processed. Please wait until it completes.",
            )
            return

        # Emit signal to parent to check model selection
        self.message_sent.emit(message, self.tab_index)

        # Calculate estimated cost of user message
        if self.current_model and self.cost_tracking_enabled:
            token_count = estimate_tokens(message, self.current_model)
            input_cost = calculate_message_cost(
                self.current_model, token_count, is_input=True
            )
            self.total_cost += input_cost
            self.current_message_cost = input_cost
            self.cost_updated.emit(self.total_cost)

        # Disable input while processing
        self.message_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.update_status("Sending message...")

        # Get current timestamp
        timestamp = (
            datetime.now().strftime("%H:%M:%S")
            if settings_manager.get("show_timestamps", True)
            else None
        )

        # Add user message to chat
        self.add_message(message, True, timestamp)

        # Clear input
        self.message_input.clear()

        # Start chat worker
        self.chat_worker = ChatWorker(
            message, self.current_model, self.conversation_history
        )
        self.chat_worker.message_received.connect(self.handle_ai_message_chunk)
        self.chat_worker.error_occurred.connect(self.handle_error)
        self.chat_worker.finished.connect(self.handle_chat_finished)
        self.chat_worker.start()
        self.update_status("Receiving message...")

        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        # Prepare for AI response
        self.current_ai_message = ""
        self.ai_message_widget = None

    def update_status(self, status):
        """Update status and emit signal to parent."""
        self.status_changed.emit(status, self.tab_index)

    def handle_ai_message_chunk(self, chunk: str):
        """Handle streaming AI message chunks."""
        self.current_ai_message += chunk

        # Create or update AI message widget
        if self.ai_message_widget is None:
            timestamp = (
                datetime.now().strftime("%H:%M:%S")
                if settings_manager.get("show_timestamps", True)
                else None
            )
            self.ai_message_widget = ChatMessage(
                self.current_ai_message, False, timestamp, self.current_model
            )
            self.chat_layout.insertWidget(
                self.chat_layout.count() - 1, self.ai_message_widget
            )
        else:
            # Efficiently update existing widget content
            self.ai_message_widget.update_content(self.current_ai_message)

        # Auto scroll if enabled
        if settings_manager.get("auto_scroll", True):
            QTimer.singleShot(10, self.scroll_to_bottom)

    def handle_error(self, error_message: str):
        """Handle errors from the chat worker."""
        # Check for max tokens error
        token_error_keywords = [
            "maximum context length",
            "token limit",
            "max tokens",
            "context_length_exceeded",
            "finish_reason: length",
        ]

        is_token_error = any(
            keyword in error_message.lower() for keyword in token_error_keywords
        )

        if is_token_error:
            self.show_error(
                "Warning: The response may have been truncated due to token limits. "
                "Consider increasing max_tokens in settings or shortening your prompt."
            )
        else:
            self.show_error(f"An error occurred: {error_message}")

        self.handle_chat_finished("error")

    def handle_chat_finished(self, finish_reason: Optional[str] = None):
        """Handle chat worker finished signal."""
        self.message_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.update_status("Ready")

        if self.current_ai_message:
            # Calculate cost of AI response
            if self.current_model and self.cost_tracking_enabled:
                token_count = estimate_tokens(
                    self.current_ai_message, self.current_model
                )
                output_cost = calculate_message_cost(
                    self.current_model, token_count, is_input=False
                )
                self.total_cost += output_cost
                self.cost_updated.emit(self.total_cost)

                # Update the AI message widget to show cost if needed
                if self.ai_message_widget and hasattr(
                    self.ai_message_widget, "set_message_cost"
                ):
                    self.ai_message_widget.set_message_cost(output_cost)

            # Add the complete AI message to conversation history
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": self.current_ai_message,
                    "model": self.current_model,
                }
            )
            if finish_reason == "length":
                timestamp = (
                    datetime.now().strftime("%H:%M:%S")
                    if settings_manager.get("show_timestamps", True)
                    else None
                )
                self.add_message(
                    "Warning: The response may have been truncated due to reaching the maximum token limit. Increase your max tokens via Settings -> Preferences -> Chat -> Max Tokens. ",
                    False,
                    timestamp,
                    "System",
                )

        # Properly clean up the worker
        if self.chat_worker:
            try:
                if self.chat_worker.isRunning():
                    self.chat_worker.stop_safely()
            except Exception as e:
                logging.error(f"Error cleaning up chat worker: {e}")
            finally:
                self.chat_worker = None

        if settings_manager.get("auto_scroll", True):
            self.scroll_to_bottom()

    def add_message(
        self,
        message: str,
        is_user: bool,
        timestamp: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """Add a message to the chat display."""
        message_widget = ChatMessage(message, is_user, timestamp, model_name)

        # Connect edit signal for user messages
        if is_user:
            message_widget.edit_requested.connect(self.handle_edit_request)
            message_widget.resend_requested.connect(self.handle_resend_request)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message_widget)

        # Auto scroll if enabled
        if settings_manager.get("auto_scroll", True):
            QTimer.singleShot(10, self.scroll_to_bottom)

    def handle_resend_request(self, message_widget):
        """Handle resend request for a message."""
        self.update_last_message(message_widget)

    def handle_edit_request(self, message_widget):
        """Handle edit request for a message."""
        # Check if a worker is already running
        if self.chat_worker is not None and self.chat_worker.isRunning():
            QMessageBox.warning(
                self,
                "Processing",
                "Cannot edit while an AI response is being processed. Please wait until it completes.",
            )
            return

        # Get the original message text
        original_text = message_widget.raw_content

        # Show edit dialog with word wrap enabled
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Message")
        dlg_layout = QVBoxLayout(dialog)

        label = QLabel("Edit your message:", dialog)
        dlg_layout.addWidget(label)

        text_edit = QTextEdit(dialog)
        text_edit.setPlainText(original_text)
        # Enable word wrap at widget width
        text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        text_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        dlg_layout.addWidget(text_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Orientation.Horizontal,
            dialog,
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dlg_layout.addWidget(buttons)

        if dialog.exec_() == QDialog.Accepted:
            text = text_edit.toPlainText()
            ok = True
        else:
            text = original_text
            ok = False

        if ok and text.strip():
            self.update_last_message(message_widget, text)

    def update_last_message(self, message_widget, text=""):
        """Update last message in a tab."""
        # Find the position of this message in the layout
        message_index = -1
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item and item.widget() == message_widget:
                message_index = i
                break

        if message_index != -1:
            # First, remove all messages after this one
            self.remove_messages_after_index(message_index)

            # Then, also remove the current message widget
            self.chat_layout.removeWidget(message_widget)
            message_widget.deleteLater()

            # Update conversation history to exclude this message and all after it
            self.update_conversation_history_to_index(message_index - 1)

        # Send the edited message to get a new response
        self.message_input.setText(
            text.strip() if text != "" else message_widget.raw_content
        )
        self.send_message()

    def remove_messages_after_index(self, index, include_current=False):
        """Remove all message widgets after the given index."""
        # Skip the suggestions widget and stretch at the end
        items_to_remove = []

        # Determine starting index based on whether to include current message
        start_index = index if include_current else index + 1

        for i in range(start_index, self.chat_layout.count() - 1):
            item = self.chat_layout.itemAt(i)
            if item and isinstance(item.widget(), ChatMessage):
                items_to_remove.append(item)

        for item in items_to_remove:
            widget = item.widget()
            self.chat_layout.removeWidget(widget)
            widget.deleteLater()

    def update_conversation_history_to_index(
        self, message_index, exclude_current=False
    ):
        """Update conversation history to match messages up to the given index."""
        # Count user and AI messages up to the index
        user_count = 0
        ai_count = 0

        # Count up to but not including the current message if exclude_current is True
        count_limit = message_index if exclude_current else message_index + 1

        for i in range(count_limit):
            item = self.chat_layout.itemAt(i)
            if item and isinstance(item.widget(), ChatMessage):
                widget = item.widget()
                if widget.is_user_message:
                    user_count += 1
                else:
                    ai_count += 1

        # Trim conversation history to match
        new_history = []
        current_user_count = 0
        current_ai_count = 0

        for msg in self.conversation_history:
            if msg["role"] == "user":
                if current_user_count < user_count:
                    new_history.append(msg)
                    current_user_count += 1
                else:
                    break
            elif msg["role"] == "assistant":
                if current_ai_count < ai_count:
                    new_history.append(msg)
                    current_ai_count += 1
                else:
                    break

        self.conversation_history = new_history

    def scroll_to_bottom(self):
        """Scroll the chat to the bottom."""
        scrollbar = self.chat_scroll.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def clear_chat(self):
        """Clear the chat history but keep suggestion widget and stretch."""
        # If suggestions exist, preserve suggestions_widget at index 0
        if hasattr(self, "suggestions_widget"):
            # Remove only message widgets (between suggestions and stretch)
            while self.chat_layout.count() > 2:
                child_item = self.chat_layout.takeAt(1)
                if child_item:
                    widget = child_item.widget()
                    if widget:
                        widget.deleteLater()
        else:
            # Fallback: remove all widgets except stretch
            while self.chat_layout.count() > 1:
                child_item = self.chat_layout.takeAt(0)
                if child_item:
                    widget = child_item.widget()
                    if widget:
                        widget.deleteLater()

        # Clear conversation history and update status
        self.conversation_history.clear()
        self.update_status("Chat cleared")

        # Reset cost tracking
        self.total_cost = 0.0
        self.cost_updated.emit(self.total_cost)

        # Re-show suggestion widget if present
        if hasattr(self, "suggestions_widget"):
            # Ensure it's in layout
            if self.chat_layout.indexOf(self.suggestions_widget) == -1:
                self.chat_layout.insertWidget(0, self.suggestions_widget)
            self.suggestions_widget.show()

    def show_error(self, message: str):
        """Show an error message."""
        QMessageBox.critical(self.parent, "Error", message)
        self.update_status(f"Error: {message}")

    def refresh_styles(self):
        """Refresh the style of all chat messages."""
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item:
                widget = item.widget()
                if isinstance(widget, ChatMessage):
                    widget.refresh_style()
        # Also update font if method is available
        if self.parent and hasattr(self.parent, "font"):
            self.update_font_recursive(self.parent.font())

    def update_font_recursive(self, font: QFont):
        """Recursively update font for this tab and its children."""
        self.setFont(font)
        self.message_input.setFont(font)
        self.send_button.setFont(font)

        if hasattr(self, "suggestions_widget"):
            self.suggestions_widget.setFont(font)
            for child_widget in self.suggestions_widget.findChildren(QWidget):
                child_widget.setFont(font)

        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, ChatMessage):
                    widget.update_font_recursive(font)
                elif isinstance(widget, QLabel) or isinstance(
                    widget, QPushButton
                ):  # e.g. suggestion label
                    widget.setFont(font)

    def closeEvent(self, event):
        """Handle widget close event."""
        self.terminate_worker()
        super().closeEvent(event)

    def deleteLater(self):
        """Override deleteLater to ensure worker is terminated."""
        self.terminate_worker()
        super().deleteLater()

    def __del__(self):
        """Destructor to ensure worker cleanup."""
        try:
            self.terminate_worker()
        except Exception:
            # Ignore errors during destruction
            pass

    def load_conversation_history(self, conversation_history):
        """Load conversation history from imported data."""

        # Clear any existing messages first
        self.clear_chat()

        # Set the conversation history
        self.conversation_history = conversation_history.copy()

        # Create message widgets for each message
        for msg in conversation_history:
            role = msg.get("role")
            content = msg.get("content", "")
            model = msg.get("model")

            if not content:
                continue

            # Determine if message is from user
            is_user = role == "user"

            # Add message widget (don't add timestamp for imported messages)
            message_widget = ChatMessage(
                content, is_user, None, model if not is_user else None
            )

            # Connect edit signal for user messages
            if is_user:
                message_widget.edit_requested.connect(self.handle_edit_request)
                message_widget.resend_requested.connect(self.handle_resend_request)

            self.chat_layout.insertWidget(self.chat_layout.count() - 1, message_widget)

        # Remember to set the model if the last message has one
        for msg in reversed(conversation_history):
            if msg.get("role") == "assistant" and msg.get("model"):
                self.current_model = msg.get("model")
                break

        # Hide suggestions
        if hasattr(self, "suggestions_widget") and self.suggestions_widget.isVisible():
            self.suggestions_widget.hide()

        # Scroll to show the conversation
        QTimer.singleShot(100, self.scroll_to_bottom)

    def get_total_cost(self):
        """Return the total cost for this chat session."""
        return self.total_cost
