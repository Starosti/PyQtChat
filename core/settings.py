"""
Settings management for the PyQtChat application.
"""

import os
import logging
from PyQt5.QtCore import QSettings
from typing import Dict, List, Any, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
    logging.info("Loaded environment variables from .env file")
except ImportError:
    logging.info(
        "python-dotenv not installed. To load API keys from .env file, install it with: pip install python-dotenv"
    )
except FileNotFoundError:
    logging.debug(
        ".env file not found - this is normal if you're using the settings dialog for API keys"
    )
except PermissionError:
    logging.warning("Permission denied reading .env file - check file permissions")
except Exception as e:
    logging.warning(f"Error loading .env file: {e}")


class SettingsManager:
    """Centralized settings management for the application."""

    def __init__(self):
        """Initialize settings manager with QSettings."""
        self.settings = QSettings("PyQtChat", "Starosti")
        self.defaults = {
            "openai_key": "",
            "anthropic_key": "",
            "google_key": "",
            "openrouter_key": "",
            "custom_models": "",
            "api_base_url": "",
            "dark_mode": False,
            "font_size": 10,
            "auto_scroll": True,
            "show_timestamps": True,
            "max_tokens": 2000,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        try:
            if default is None and key in self.defaults:
                default = self.defaults[key]

            # For boolean values, explicitly convert
            if isinstance(default, bool):
                return self.settings.value(key, default, type=bool)
            # For integer values
            elif isinstance(default, int):
                return self.settings.value(key, default, type=int)
            # For other types
            else:
                return self.settings.value(key, default)
        except Exception as e:
            logging.error(f"Error reading setting '{key}': {e}")
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a setting value by key."""
        try:
            self.settings.setValue(key, value)
            self.settings.sync()  # Ensure settings are written to disk
        except Exception as e:
            logging.error(f"Error saving setting '{key}': {e}")
            raise  # Re-raise to let calling code handle it

    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys as a dictionary."""
        return {
            "openai": self.get("openai_key", ""),
            "anthropic": self.get("anthropic_key", ""),
            "google": self.get("google_key", ""),
            "openrouter": self.get("openrouter_key", ""),
        }

    def get_custom_models(self) -> List[str]:
        """Get list of custom models."""
        custom_models_text = self.get("custom_models", "")
        if not custom_models_text:
            return []

        return [
            model.strip() for model in custom_models_text.split("\n") if model.strip()
        ]


settings_manager = SettingsManager()
