"""
Settings dialog for API configuration and preferences.
"""

import logging
import os
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QSpinBox,
    QDialogButtonBox,
)
from core.settings import settings_manager


class SettingsDialog(QDialog):
    """Settings dialog for API configuration and preferences."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Create dialog UI components."""
        layout = QVBoxLayout()

        # Create tabs
        tab_widget = QTabWidget()

        # API Configuration Tab
        api_tab = QWidget()
        api_layout = QFormLayout()

        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.Password)
        self.anthropic_key = QLineEdit()
        self.anthropic_key.setEchoMode(QLineEdit.Password)
        self.google_key = QLineEdit()
        self.google_key.setEchoMode(QLineEdit.Password)
        self.openrouter_key = QLineEdit()
        self.openrouter_key.setEchoMode(QLineEdit.Password)

        api_layout.addRow("OpenAI API Key:", self.openai_key)
        api_layout.addRow("Anthropic API Key:", self.anthropic_key)
        api_layout.addRow("Google API Key:", self.google_key)
        api_layout.addRow("OpenRouter API Key:", self.openrouter_key)

        api_tab.setLayout(api_layout)
        tab_widget.addTab(api_tab, "API Keys")

        # Custom Models Tab
        custom_models_tab = QWidget()
        custom_models_layout = QVBoxLayout()

        custom_models_label = QLabel(
            "Custom Models (Advanced)\nProvide custom models compliant to the LiteLLM model format (provider/model-name) one per line:"
        )
        custom_models_layout.addWidget(custom_models_label)

        self.custom_models_text = QTextEdit()
        self.custom_models_text.setPlaceholderText(
            "Example:\nopenrouter/microsoft/wizardlm-2-8x22b\nopenrouter/anthropic/claude-3.5-sonnet\nollama/llama3\ntogether_ai/meta-llama/Meta-Llama-3-8B-Instruct"
        )
        custom_models_layout.addWidget(self.custom_models_text)

        # Add API Base URL field
        api_base_label = QLabel(
            "API Base URL (Optional)\nCustom API endpoint for LiteLLM calls:"
        )
        custom_models_layout.addWidget(api_base_label)

        self.api_base_url = QLineEdit()
        self.api_base_url.setPlaceholderText(
            "Example: https://api.openai.com/v1 or http://localhost:8000/v1"
        )
        custom_models_layout.addWidget(self.api_base_url)

        custom_models_tab.setLayout(custom_models_layout)
        tab_widget.addTab(custom_models_tab, "Custom Models")

        # Appearance Tab
        appearance_tab = QWidget()
        appearance_layout = QFormLayout()

        self.dark_mode = QCheckBox()
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(10)

        appearance_layout.addRow("Dark Mode:", self.dark_mode)
        appearance_layout.addRow("Font Size:", self.font_size)

        appearance_tab.setLayout(appearance_layout)
        tab_widget.addTab(appearance_tab, "Appearance")

        # Chat Settings Tab
        chat_tab = QWidget()
        chat_layout = QFormLayout()

        self.auto_scroll = QCheckBox()
        self.auto_scroll.setChecked(True)
        self.show_timestamps = QCheckBox()
        self.show_timestamps.setChecked(True)
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(1, 10000)
        self.max_tokens.setValue(2000)

        chat_layout.addRow("Auto Scroll:", self.auto_scroll)
        chat_layout.addRow("Show Timestamps:", self.show_timestamps)
        chat_layout.addRow("Max Tokens:", self.max_tokens)

        chat_tab.setLayout(chat_layout)
        tab_widget.addTab(chat_tab, "Chat")

        layout.addWidget(tab_widget)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def load_settings(self):
        """Load settings from settings manager and environment variables."""
        api_keys_info = [
            ("openai_key", self.openai_key, "OPENAI_API_KEY", "Enter OpenAI API Key"),
            (
                "anthropic_key",
                self.anthropic_key,
                "ANTHROPIC_API_KEY",
                "Enter Anthropic API Key",
            ),
            (
                "google_key",
                self.google_key,
                "GEMINI_API_KEY",
                "Enter Google AI Studio API Key",
            ),
            (
                "openrouter_key",
                self.openrouter_key,
                "OPENROUTER_API_KEY",
                "Enter OpenRouter API Key",
            ),
        ]

        for (
            settings_key,
            qlineedit_widget,
            env_var_name,
            default_placeholder,
        ) in api_keys_info:
            saved_value = settings_manager.get(settings_key, "")
            env_value = os.environ.get(env_var_name)

            if saved_value:  # Value exists in QSettings
                qlineedit_widget.setText(saved_value)
                qlineedit_widget.setPlaceholderText("")  # Clear any placeholder
            elif env_value:  # No QSettings value, but env var exists
                qlineedit_widget.setText(
                    ""
                )  # Ensure field is empty to show placeholder
                qlineedit_widget.setPlaceholderText("[Using key from environment]")
            else:  # No value in QSettings or environment
                qlineedit_widget.setText("")
                qlineedit_widget.setPlaceholderText(default_placeholder)

        self.custom_models_text.setPlainText(settings_manager.get("custom_models", ""))
        self.api_base_url.setText(settings_manager.get("api_base_url", ""))
        self.dark_mode.setChecked(settings_manager.get("dark_mode", False))
        self.font_size.setValue(settings_manager.get("font_size", 10))
        self.auto_scroll.setChecked(settings_manager.get("auto_scroll", True))
        self.show_timestamps.setChecked(settings_manager.get("show_timestamps", True))
        self.max_tokens.setValue(settings_manager.get("max_tokens", 2000))

    def save_settings(self):
        """Save settings to settings manager."""
        settings_manager.set("openai_key", self.openai_key.text())
        settings_manager.set("anthropic_key", self.anthropic_key.text())
        settings_manager.set("google_key", self.google_key.text())
        settings_manager.set("openrouter_key", self.openrouter_key.text())
        settings_manager.set("custom_models", self.custom_models_text.toPlainText())
        settings_manager.set("api_base_url", self.api_base_url.text())
        settings_manager.set("dark_mode", self.dark_mode.isChecked())
        settings_manager.set("font_size", self.font_size.value())
        settings_manager.set("auto_scroll", self.auto_scroll.isChecked())
        settings_manager.set("show_timestamps", self.show_timestamps.isChecked())
        settings_manager.set("max_tokens", self.max_tokens.value())

    def accept(self):
        """Save settings when dialog is accepted."""
        try:
            self.save_settings()
            logging.info("Settings saved successfully")
            super().accept()
        except PermissionError as e:
            logging.error(f"Permission error saving settings: {e}")
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                self,
                "Settings Error",
                "Unable to save settings due to permission restrictions.\n\n"
                "This might happen if the application doesn't have write access to its configuration directory.\n"
                "Try running the application as administrator or check folder permissions.",
            )
        except OSError as e:
            logging.error(f"OS error saving settings: {e}")
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                self,
                "Settings Error",
                f"Unable to save settings due to a system error:\n{str(e)}\n\n"
                "This might be caused by insufficient disk space or system configuration issues.",
            )
        except Exception as e:
            logging.error(f"Unexpected error saving settings: {str(e)}", exc_info=True)
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(
                self,
                "Settings Error",
                f"An unexpected error occurred while saving settings:\n{str(e)}\n\n"
                f"Please check the application log for more details.",
            )
