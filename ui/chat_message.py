"""
Custom widget for displaying chat messages.
"""

import logging
from typing import Optional
from PyQt5.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QApplication,
    QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSettings
from PyQt5.QtGui import QFont

try:
    import markdown
except ImportError:
    logging.warning("Markdown not installed. Plain text will be used.")
    markdown = None

from utils.style_manager import get_current_code_style


class ChatMessage(QFrame):
    """Custom widget for displaying chat messages."""

    # Add signal for edit request
    edit_requested = pyqtSignal(object)
    resend_requested = pyqtSignal(object)

    def __init__(
        self,
        message: str,
        is_user: bool,
        timestamp: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        super().__init__()
        self.is_user_message = is_user
        self.model_name = model_name
        self.raw_content = message
        self.time_label: Optional[QLabel] = None  # Initialize
        self.edit_btn: Optional[QPushButton] = None  # Initialize
        self.setup_ui(message, is_user, timestamp, model_name)

    def setup_ui(
        self,
        message: str,
        is_user: bool,
        timestamp: Optional[str],
        model_name: Optional[str] = None,
    ):
        layout = QVBoxLayout()

        # Header with role and timestamp
        header_layout = QHBoxLayout()
        role_text = "You" if is_user else (model_name if model_name else "AI")
        self.role_label = QLabel(role_text)
        self.role_label.setStyleSheet(
            f"""
            QLabel {{
                font-weight: bold;
                color: {'#007acc' if is_user else '#28a745'};
                padding: 2px;
            }}
        """
        )

        header_layout.addWidget(self.role_label)
        header_layout.addStretch()

        if timestamp:
            self.time_label = QLabel(timestamp)
            self.time_label.setStyleSheet(
                "color: #666; font-size: 10px;"
            )  # Initial small size for timestamp
            header_layout.addWidget(self.time_label)

        # Add Edit button (only for user messages)
        if is_user:
            self.resend_btn = QPushButton("Resend")
            self.resend_btn.setToolTip("Resend this message")
            self.resend_btn.clicked.connect(self.request_resend)
            header_layout.addWidget(self.resend_btn)

            self.edit_btn = QPushButton("Edit")
            self.edit_btn.setToolTip("Edit this message")
            self.edit_btn.clicked.connect(self.request_edit)
            header_layout.addWidget(self.edit_btn)

        # Add Copy button
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setToolTip("Copy message to clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        header_layout.addWidget(self.copy_btn)

        layout.addLayout(header_layout)

        # Add horizontal line under header
        self.hr = QFrame()
        self.hr.setFrameShape(QFrame.HLine)
        self.hr.setFrameShadow(QFrame.Sunken)
        self.hr.setFixedHeight(1)

        # Get the dark mode setting for initial styling
        settings = QSettings("PyQtChat", "Starosti")
        dark_mode = settings.value("dark_mode", False, type=bool)

        # Style the horizontal line based on theme
        if dark_mode:
            self.hr.setStyleSheet("QFrame { background-color: #555555; border: none; }")
        else:
            self.hr.setStyleSheet("QFrame { background-color: #cccccc; border: none; }")

        layout.addWidget(self.hr)

        # Message content
        self.message_content_label = QLabel()
        self.message_content_label.setWordWrap(True)
        self.message_content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.message_content_label.setTextFormat(Qt.TextFormat.RichText)
        self.update_content(message)

        # Apply initial styling
        self.refresh_style()

        layout.addWidget(self.message_content_label)
        self.setLayout(layout)

    def request_edit(self):
        """Request edit for this message."""
        self.edit_requested.emit(self)

    def request_resend(self):
        """Request resend for this message."""
        self.resend_requested.emit(self)

    def update_content(self, new_content: str):
        """Efficiently update the message content, rendering Markdown if available."""
        self.raw_content = new_content
        current_font = self.font()  # Get the widget's current font
        font_family = current_font.family()
        font_size_pt = current_font.pointSize()

        # Ensure font family with spaces is quoted for CSS
        font_family_css = f"'{font_family}'" if " " in font_family else font_family

        body_font_style = (
            f"body {{ font-family: {font_family_css}; font-size: {font_size_pt}pt; }}"
        )

        if markdown:
            try:
                html_body = markdown.markdown(
                    new_content, extensions=["pymdownx.extra", "pymdownx.highlight"]
                )
                # Wrap with HTML and include CSS (code style + body font style)
                combined_css = f"{get_current_code_style()} {body_font_style}"
                html_full = f"<html><head><style>{combined_css}</style></head><body>{html_body}</body></html>"
                self.message_content_label.setText(html_full)
            except Exception as e:
                logging.error(f"Markdown rendering error: {e}")
                # Fallback: Apply font style directly if possible, or just set text
                self.message_content_label.setText(
                    f"<div style='font-family: {font_family_css}; font-size: {font_size_pt}pt;'>{new_content}</div>"
                )
        else:
            # Apply font style directly for plain text
            self.message_content_label.setText(
                f"<div style='font-family: {font_family_css}; font-size: {font_size_pt}pt;'>{new_content}</div>"
            )

    def refresh_style(self):
        """Refresh the style of the message content based on the current theme."""
        # Re-render content with updated CSS for code highlighting and body font
        self.update_content(self.raw_content)

        # Get the dark mode setting
        settings = QSettings("PyQtChat", "Starosti")
        dark_mode = settings.value("dark_mode", False, type=bool)

        # Update horizontal line styling
        if dark_mode:
            self.hr.setStyleSheet("QFrame { background-color: #555555; border: none; }")
        else:
            self.hr.setStyleSheet("QFrame { background-color: #cccccc; border: none; }")

        # Different styling for light and dark mode
        if dark_mode:
            self.message_content_label.setStyleSheet(
                f"""
            QLabel {{
                background-color: {'#1a3f5f' if self.is_user_message else '#2d2d2d'};
                border: 1px solid {'#1e4a6b' if self.is_user_message else '#3d3d3d'};
                border-radius: 8px;
                padding: 10px;
                margin: 2px;
                color: #ffffff;
            }}
            """
            )
        else:
            self.message_content_label.setStyleSheet(
                f"""
            QLabel {{
                background-color: {'#e1f5fe' if self.is_user_message else '#f5f5f5'};
                border: 1px solid {'#b3e5fc' if self.is_user_message else '#ddd'};
                border-radius: 8px;
                padding: 10px;
                margin: 2px;
            }}
            """
            )

    def update_font_recursive(self, font: QFont):
        """Update font for this message widget and its relevant children."""
        self.setFont(font)
        self.role_label.setFont(font)

        # For timestamp, we might want it to remain smaller or scale differently.
        # For now, let's apply the main font, but adjust its point size.
        if self.time_label:
            time_font = QFont(font)
            # Keep timestamp font size relative or fixed, e.g., 2 points smaller or fixed at 8-10pt
            current_main_font_size = font.pointSize()
            timestamp_font_size = max(
                8, current_main_font_size - 2
            )  # Example: 2pts smaller, min 8
            if (
                current_main_font_size <= 10
            ):  # if main font is small, keep timestamp smaller
                timestamp_font_size = 8
            time_font.setPointSize(timestamp_font_size)
            self.time_label.setFont(time_font)

        self.message_content_label.setFont(font)  # Base font for the QLabel
        self.copy_btn.setFont(font)
        if self.edit_btn:
            self.edit_btn.setFont(font)

        # Crucially, re-render the HTML content to embed the new font size
        self.update_content(self.raw_content)

    def copy_to_clipboard(self):
        """Copy the original message text to the clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self.raw_content)

            # Show feedback
            original_text = self.copy_btn.text()
            self.copy_btn.setText("Copied!")
            self.copy_btn.setEnabled(False)

            # Reset button after 1.5 seconds
            QTimer.singleShot(1500, lambda: self.reset_copy_button(original_text))
        else:
            # Show error message if clipboard is not available
            QMessageBox.warning(
                None, "Clipboard Error", "Could not access the clipboard."
            )

    def reset_copy_button(self, original_text):
        """Reset the copy button to its original state."""
        self.copy_btn.setText(original_text)
        self.copy_btn.setEnabled(True)
