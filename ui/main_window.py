"""
Main application window for the PyQtChat.
"""

import logging
from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QSplitter,
    QFrame,
    QAction,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QApplication,  # Added QApplication
)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QFont, QCloseEvent

from ui.settings_dialog import SettingsDialog
from ui.chat_tab import ChatTab
from core.chat_worker import ChatWorker
from core.models import model_manager
from core.settings import settings_manager
from utils.export import export_chat
from utils.style_manager import get_app_stylesheet
from utils.cost_tracker import get_model_cost_display


class ChatbotApp(QMainWindow):
    """Main application window for the PyQtChat."""

    def __init__(self):
        super().__init__()
        self.settings = QSettings("PyQtChat", "Starosti")
        self.chat_tabs = []  # List of ChatTab objects
        self.current_tab_index = -1  # Index of currently active tab

        self.apply_theme()
        self.setup_ui()
        self.setup_menu()
        self.load_settings()
        self.populate_models()

        # Create initial tab
        self.create_new_chat_tab("New Chat")

    def setup_ui(self):
        """Set up the main user interface."""
        self.setWindowTitle("PyQtChat")
        self.setGeometry(100, 100, 1200, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(
            10, 10, 10, 10
        )  # Add margins around main content

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)  # Add spacing between panels

        # Left sidebar for chat tabs
        self.sidebar = QWidget()
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(300)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(
            10, 10, 5, 10
        )  # Add margins with less spacing on right

        # Tab list header with new chat button
        tab_header = QHBoxLayout()
        tab_header.addWidget(QLabel("Chats"))

        new_chat_btn = QPushButton("New Chat")
        new_chat_btn.clicked.connect(lambda: self.create_new_chat_tab("New Chat"))  # type: ignore
        tab_header.addWidget(new_chat_btn)

        sidebar_layout.addLayout(tab_header)

        # Tab list
        self.tab_list = QListWidget()
        self.tab_list.currentRowChanged.connect(self.switch_chat_tab)
        self.tab_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_list.customContextMenuRequested.connect(self.show_tab_context_menu)
        sidebar_layout.addWidget(self.tab_list)

        splitter.addWidget(self.sidebar)

        # Middle panel for chat content
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(
            5, 10, 5, 10
        )  # Add margins with spacing on sides

        # Add information bar at the top of content area
        self.info_bar = QWidget()
        info_bar_layout = QHBoxLayout(self.info_bar)
        info_bar_layout.setContentsMargins(5, 2, 5, 2)

        # Tab title label
        self.tab_title_label = QLabel("No chat selected")
        self.tab_title_label.setStyleSheet("font-weight: bold;")
        info_bar_layout.addWidget(self.tab_title_label)

        info_bar_layout.addStretch()

        # Move total cost label to info bar
        self.total_cost_label = QLabel("Total cost: $0.00")
        info_bar_layout.addWidget(self.total_cost_label)

        # Add separator line below info bar
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setMaximumHeight(1)

        # Add info bar and separator to content layout
        self.content_layout.addWidget(self.info_bar)
        self.content_layout.addWidget(separator)

        splitter.addWidget(self.content_area)

        # Right panel (controls)
        control_panel = self.create_control_panel()
        control_panel.setMinimumWidth(200)
        control_panel.setMaximumWidth(300)
        splitter.addWidget(control_panel)

        # Set splitter proportions
        splitter.setSizes([200, 700, 100])

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

    def create_control_panel(self):
        """Create the control panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(
            5, 10, 10, 10
        )  # Add margins with less spacing on left

        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QVBoxLayout()

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(model_manager.get_providers())
        self.provider_combo.currentTextChanged.connect(self.populate_models)

        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.update_cost_display)

        model_layout.addWidget(QLabel("Provider:"))
        model_layout.addWidget(self.provider_combo)
        model_layout.addWidget(QLabel("Model:"))
        model_layout.addWidget(self.model_combo)

        # Add cost display
        self.cost_label = QLabel("Cost: Not available")
        self.cost_label.setWordWrap(True)
        model_layout.addWidget(self.cost_label)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Chat controls
        controls_group = QGroupBox("Chat Controls")
        controls_layout = QVBoxLayout()

        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.clicked.connect(self.clear_current_chat)

        self.export_button = QPushButton("Export Chat")
        self.export_button.clicked.connect(self.export_current_chat)

        self.import_button = QPushButton("Import Chat")
        self.import_button.clicked.connect(self.import_chat)

        controls_layout.addWidget(self.clear_button)
        controls_layout.addWidget(self.export_button)
        controls_layout.addWidget(self.import_button)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)

        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Add stretch to push everything to top
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def setup_menu(self):
        """Set up the application menu."""
        menubar = self.menuBar()

        if not menubar:
            return

        # File menu
        file_menu = menubar.addMenu("File")

        if not file_menu:
            return

        # Add create chat action
        create_action = QAction("Create A New Chat", self)
        create_action.setShortcut("Ctrl+N")
        create_action.triggered.connect(lambda: self.create_new_chat_tab("New Chat"))  # type: ignore
        file_menu.addAction(create_action)

        file_menu.addSeparator()

        import_action = QAction("Import Chat", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_chat)
        file_menu.addAction(import_action)

        export_action = QAction("Export Chat", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_current_chat)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Add delete chat action
        delete_action = QAction("Delete Current Chat", self)
        delete_action.setShortcut("Ctrl+D")
        delete_action.triggered.connect(self.delete_current_chat)
        file_menu.addAction(delete_action)

        # Add rename chat action
        rename_action = QAction("Rename Current Chat", self)
        rename_action.setShortcut("F2")
        rename_action.triggered.connect(self.rename_current_chat)
        file_menu.addAction(rename_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self._handle_exit_action)
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        if not settings_menu:
            return

        preferences_action = QAction("Preferences", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_settings)
        settings_menu.addAction(preferences_action)

        theme_action = QAction("Toggle Theme", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self.toggle_theme)
        settings_menu.addAction(theme_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        if not help_menu:
            return

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_new_chat_tab(self, title="New Chat"):
        """Create a new chat tab with the given title."""
        # Create the chat tab
        chat_tab = ChatTab(self)
        chat_tab.message_sent.connect(self.handle_message_sent)
        chat_tab.status_changed.connect(self.update_status)
        chat_tab.set_tab_index(len(self.chat_tabs))

        # Connect cost tracking signal
        chat_tab.cost_updated.connect(self.update_total_cost_display)

        # Add to our list of tabs
        self.chat_tabs.append(chat_tab)

        # Add to UI
        self.content_layout.addWidget(chat_tab)
        if len(self.chat_tabs) > 1:  # Hide previous tab
            self.chat_tabs[self.current_tab_index].setVisible(False)

        # Add to sidebar list
        list_item = QListWidgetItem(title)
        self.tab_list.addItem(list_item)

        # Select the new tab
        self.current_tab_index = len(self.chat_tabs) - 1
        self.tab_list.setCurrentRow(self.current_tab_index)

        return chat_tab

    def switch_chat_tab(self, index):
        """Switch to the chat tab at the given index."""
        if index < 0 or index >= len(self.chat_tabs):
            return

        # Hide current tab if there is one
        if self.current_tab_index >= 0 and self.current_tab_index < len(self.chat_tabs):
            self.chat_tabs[self.current_tab_index].setVisible(False)

        # Show selected tab
        self.chat_tabs[index].setVisible(True)
        self.current_tab_index = index

        # Update status
        status = self.chat_tabs[index].get_status()
        if status:
            self.status_label.setText(status)
        else:
            self.status_label.setText("Ready")

        # Update total cost display and tab title in info bar
        if hasattr(self.chat_tabs[index], "get_total_cost"):
            tab_cost = self.chat_tabs[index].get_total_cost()
            self.update_total_cost_display(tab_cost)

        # Update tab title in info bar
        if index < self.tab_list.count():
            item = self.tab_list.item(index)
            if item is not None:
                title = item.text()
                self.tab_title_label.setText(title)

    def show_tab_context_menu(self, position):
        """Show context menu for tab list items."""
        if self.tab_list.count() == 0:
            return

        menu = QMenu()
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        action = menu.exec_(self.tab_list.mapToGlobal(position))

        index = self.tab_list.currentRow()
        if index < 0:
            return

        if action == rename_action:
            self.rename_chat_tab(index)
        elif action == delete_action:
            self.delete_chat_tab(index)

    def rename_chat_tab(self, index):
        """Rename the chat tab at the given index."""
        if index < 0 or index >= len(self.chat_tabs):
            return

        item = self.tab_list.item(index)
        if item is None:
            return

        current_title = item.text()
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Rename Chat")
        dialog.setLabelText("Enter new name:")
        dialog.setTextValue(current_title)
        dialog.resize(200, 150)
        ok = dialog.exec_()
        new_title = dialog.textValue()

        if ok and new_title:
            item = self.tab_list.item(index)
            if item is None:
                return
            item.setText(new_title)
            # Update info bar title if this is the current tab
            if index == self.current_tab_index:
                self.tab_title_label.setText(new_title)

    def rename_current_chat(self):
        """Rename the currently active chat tab."""
        self.rename_chat_tab(self.current_tab_index)

    def delete_chat_tab(self, index):
        """Delete the chat tab at the given index."""
        if index < 0 or index >= len(self.chat_tabs):
            return

        if len(self.chat_tabs) == 1:
            QMessageBox.warning(
                self, "Cannot Delete", "Cannot delete the only remaining chat tab."
            )
            return
        item = self.tab_list.item(index)
        if item is None:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{item.text()}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm != QMessageBox.Yes:
            return

        # Get the tab to delete
        tab_to_delete = self.chat_tabs[index]

        # First, terminate any running thread
        tab_to_delete.terminate_worker()

        # Remove from UI
        self.tab_list.takeItem(index)

        # Remove from our list of tabs
        self.chat_tabs.pop(index)

        # Delete the widget properly
        tab_to_delete.setParent(None)
        tab_to_delete.deleteLater()

        # Update current index and tab indices
        if self.current_tab_index == index:
            # If we deleted the current tab, switch to another
            new_index = min(index, len(self.chat_tabs) - 1)
            self.tab_list.setCurrentRow(new_index)
        elif self.current_tab_index > index:
            # If we deleted a tab before the current one, adjust index
            self.current_tab_index -= 1

        # Update tab indices for all tabs after the deleted one
        for i in range(index, len(self.chat_tabs)):
            self.chat_tabs[i].set_tab_index(i)

    def delete_current_chat(self):
        """Delete the currently active chat tab."""
        self.delete_chat_tab(self.current_tab_index)

    def handle_message_sent(self, message, tab_index):
        """Handle when a message is sent from a chat tab."""
        # Get the model from control panel
        model = self.model_combo.currentText()
        if not model:
            self.show_error("Please select a model first.")
            return

        # Set the model on the tab that sent the message
        self.chat_tabs[tab_index].set_model(model)

        # Update cost display when sending a message
        self.update_cost_display()

        # If this is the first message, generate a title for the tab
        if len(self.chat_tabs[tab_index].conversation_history) == 0:
            # We'll generate the title after the first message is sent
            # For now, use a placeholder based on the message
            placeholder = message[:20] + "..." if len(message) > 20 else message
            item = self.tab_list.item(tab_index)
            if item is None:
                return
            item.setText(placeholder)

            # Schedule title generation
            QTimer.singleShot(500, lambda: self.generate_tab_title(message, tab_index))

    def generate_tab_title(self, message, tab_index):
        """Generate a title for the chat tab based on the first message."""
        # Use the same model that the chat is using
        model = self.chat_tabs[tab_index].current_model
        if not model:
            return

        # Prevent multiple title workers
        if (
            hasattr(self, "title_worker")
            and self.title_worker is not None
            and self.title_worker.isRunning()
        ):
            return

        logging.info(f"Generating title for {message}")

        # Store the worker reference
        self.title_worker = ChatWorker(
            f"Generate a very brief title (3-5 words, 20 characters max) for a chat. "
            f"Give only and only the non formatted title. Do not put any description "
            f"before or after the title.: '{message}'",
            model,
            [],  # Empty conversation history for title generation
        )

        # Stored completed title text
        title_text = ""

        def handle_title_chunk(chunk):
            nonlocal title_text
            title_text += chunk

        def handle_title_finished(reason):
            # Clean up the title (remove quotes, limit length)
            clean_title = title_text.strip().strip("\"'")
            if len(clean_title) > 30:
                clean_title = clean_title[:27] + "..."

            # Update the tab title
            if tab_index < self.tab_list.count():
                item = self.tab_list.item(tab_index)
                if item is None:
                    return
                item.setText(clean_title)
                # Update info bar title if this is the current tab
                if tab_index == self.current_tab_index:
                    self.tab_title_label.setText(clean_title)

            # Worker will clean itself up, just clear our reference
            self.title_worker = None

        # Connect signals
        self.title_worker.message_received.connect(handle_title_chunk)
        self.title_worker.finished.connect(handle_title_finished)

        # Start the worker
        self.title_worker.start()

    def update_status(self, status, tab_index):
        """Update status label when a tab's status changes."""
        if tab_index == self.current_tab_index:
            self.status_label.setText(status)

    def update_cost_display(self):
        """Update the cost display label based on selected model."""
        model = self.model_combo.currentText()
        if not model:
            self.cost_label.setText("Cost: Not available")
            return

        cost_display = get_model_cost_display(model)
        self.cost_label.setText(cost_display)

        # Update current tab's model cost info
        if self.current_tab_index >= 0 and self.current_tab_index < len(self.chat_tabs):
            self.chat_tabs[self.current_tab_index].set_current_model_cost_info(model)

    def update_total_cost_display(self, total_cost):
        """Update the total cost display."""
        self.total_cost_label.setText(f"Total cost: ${total_cost:.6f}")

    def populate_models(self):
        """Populate the model dropdown based on selected provider."""
        provider = self.provider_combo.currentText()
        self.model_combo.clear()
        models = model_manager.get_models_for_provider(provider)
        if models:
            self.model_combo.addItems(models)
            # Update cost display after populating models
            self.update_cost_display()

    def clear_current_chat(self):
        """Clear the current chat tab."""
        if self.current_tab_index >= 0 and self.current_tab_index < len(self.chat_tabs):
            # Show confirmation dialog
            confirm = QMessageBox.question(
                self,
                "Confirm Clear",
                "Are you sure you want to clear this chat? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,  # Default is No (safer option)
            )

            if confirm == QMessageBox.Yes:
                self.chat_tabs[self.current_tab_index].clear_chat()

    def export_current_chat(self):
        """Export the current chat's history."""
        if self.current_tab_index < 0 or self.current_tab_index >= len(self.chat_tabs):
            return

        chat_tab = self.chat_tabs[self.current_tab_index]
        if not chat_tab.conversation_history:
            QMessageBox.information(self, "Export Chat", "No chat history to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chat History",
            f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "JSON Files (*.json);;Text Files (*.txt);;Markdown Files (*.md);;All Files (*)",
        )

        if filename:
            success, error = export_chat(chat_tab.conversation_history, filename)
            if success:
                QMessageBox.information(
                    self, "Export Successful", f"Chat history exported to {filename}"
                )
            else:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export chat history: {error}"
                )

    def import_chat(self):
        """Import a previously exported chat file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Chat",
            "",
            "JSON Files (*.json);;Text Files (*.txt);;Markdown Files (*.md);;All Files (*)",
        )

        if not filename:
            return

        from utils.export import import_chat

        success, conversation_history, error = import_chat(filename)

        if not success:
            QMessageBox.critical(
                self, "Import Error", f"Failed to import chat: {error}"
            )
            return

        if not conversation_history:
            QMessageBox.warning(
                self, "Import Warning", "No messages found in the imported file."
            )
            return

        # Get the first message to use as a tab title base
        first_message = ""
        for msg in conversation_history:
            if msg.get("role") == "user" and msg.get("content"):
                first_message = msg["content"]
                break

        # Create a tab title from the first message or filename
        if first_message:
            title_base = (
                first_message[:20] + "..." if len(first_message) > 20 else first_message
            )
            tab_title = f"Imported: {title_base}"
        else:
            # Use filename as fallback
            import os

            basename = os.path.basename(filename)
            tab_title = f"Imported: {basename}"

        # Create a new chat tab
        chat_tab = self.create_new_chat_tab(tab_title)

        # Set the conversation history
        chat_tab.load_conversation_history(conversation_history)

        QMessageBox.information(
            self, "Import Successful", f"Chat history imported from {filename}"
        )

    def show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec_():
            # Order: Apply theme (stylesheet), then load settings (font), then UI updates
            self.apply_theme()  # Re-apply theme with potentially new dark_mode
            self.load_settings()  # Re-load all settings, including font_size, and apply them

            # Reload custom models and repopulate the dropdowns
            model_manager.reload()
            self.provider_combo.clear()
            self.provider_combo.addItems(model_manager.get_providers())
            self.populate_models()

            # Refresh styles on all tabs (for code highlighting, etc.)
            for tab in self.chat_tabs:
                tab.refresh_styles()

    def load_settings(self):
        """Load application settings."""
        # Apply font size
        font_size = settings_manager.get("font_size", 10)
        font = QFont()
        font.setPointSize(font_size)
        self.setFont(font)
        QApplication.setFont(font)  # Apply font application-wide

        # Explicitly update font for existing tabs and their contents
        for tab in self.chat_tabs:
            if hasattr(tab, "update_font_recursive"):
                tab.update_font_recursive(font)

        self.apply_theme()

    def apply_theme(self):
        """Apply the selected theme."""
        dark_mode = settings_manager.get("dark_mode", False)
        self.setStyleSheet(get_app_stylesheet(dark_mode))

        # Only style the info bar and separator if they exist
        if hasattr(self, "info_bar") and hasattr(self, "content_area"):
            # Style the info bar and separator based on theme
            if dark_mode:
                self.info_bar.setStyleSheet("background-color: #2d2d2d;")
                for frame in self.content_area.findChildren(QFrame):
                    if frame.frameShape() == QFrame.HLine:
                        frame.setStyleSheet("background-color: #555555; border: none;")
            else:
                self.info_bar.setStyleSheet("background-color: #f5f5f5;")
                for frame in self.content_area.findChildren(QFrame):
                    if frame.frameShape() == QFrame.HLine:
                        frame.setStyleSheet("background-color: #cccccc; border: none;")

        # Refresh styles on all tabs
        for tab in self.chat_tabs:
            tab.refresh_styles()
            # Also update font if tab exists and method is available
            if hasattr(tab, "update_font_recursive") and hasattr(self, "font"):
                current_font = self.font()  # Get current main window font
                if current_font.pointSize() != settings_manager.get(
                    "font_size", 10
                ):  # check if font needs update
                    new_font = QFont()
                    new_font.setPointSize(settings_manager.get("font_size", 10))
                    current_font = new_font
                tab.update_font_recursive(current_font)

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        current_dark = settings_manager.get("dark_mode", False)
        settings_manager.set("dark_mode", not current_dark)
        self.apply_theme()

    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About PyQtChat",
            """<h3>AI Chatbot Desktop Application</h3>
            <p>Version 1.0</p>
            <p>A modern desktop chatbot application powered by:</p>
            <ul>
            <li><b>PyQt5</b> - Cross-platform GUI toolkit</li>
            <li><b>LiteLLM</b> - Unified interface for 100+ LLM APIs</li>
            </ul>
            <h4> Credits: </h4>
            <p>
            <b>Starosti</b> - <a href="https://github.com/Starosti/" style="text-decoration:none; color:#3498db;">https://github.com/Starosti/</a>
            </p>
            """,
        )

    def show_error(self, message: str):
        """Show an error message."""
        QMessageBox.critical(self, "Error", message)
        self.status_label.setText(f"Error: {message}")

    def _handle_exit_action(self):
        """Handle exit action from menu."""
        self.close()

    def closeEvent(self, event: Optional[QCloseEvent] = None):
        """Handle the main window close event."""
        if not event:
            return

        # Check if any tab has a running worker or if title worker is running
        any_running = False
        workers_to_check = []

        # Check tab workers
        for tab in self.chat_tabs:
            if tab.chat_worker and tab.chat_worker.isRunning():
                any_running = True
                workers_to_check.append(tab.chat_worker)

        # Check title worker
        if (
            hasattr(self, "title_worker")
            and self.title_worker
            and self.title_worker.isRunning()
        ):
            any_running = True
            workers_to_check.append(self.title_worker)

        if any_running:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "One or more AI responses are currently being generated. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                # Terminate all workers and wait for them to finish
                self._cleanup_all_workers()
                event.accept()
            else:
                event.ignore()
        else:
            # No workers running, safe to close
            self._cleanup_all_workers()
            event.accept()

    def _cleanup_all_workers(self):
        """Clean up all running workers before application exit."""
        workers_to_cleanup = []

        # Collect all running workers
        for tab in self.chat_tabs:
            if tab.chat_worker and tab.chat_worker.isRunning():
                workers_to_cleanup.append(tab.chat_worker)

        if (
            hasattr(self, "title_worker")
            and self.title_worker
            and self.title_worker.isRunning()
        ):
            workers_to_cleanup.append(self.title_worker)

        # Terminate all workers
        for worker in workers_to_cleanup:
            if worker.isRunning():
                worker.stop_safely()

        # Wait for all workers to finish (with timeout)
        for worker in workers_to_cleanup:
            if worker.isRunning():
                if not worker.wait(3000):  # 3 second timeout
                    logging.warning(
                        f"Worker did not terminate gracefully, forcing termination"
                    )
                    worker.terminate()
                    worker.wait()

        # Clean up tab workers
        for tab in self.chat_tabs:
            tab.terminate_worker()

        # Clean up title worker
        if hasattr(self, "title_worker"):
            self.title_worker = None
