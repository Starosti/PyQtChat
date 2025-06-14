"""
PyQtChat Desktop Application - Main Entry Point

This file serves as the entry point for the application, initializing the
QApplication and launching the main window.
"""

import sys
from ui.main_window import ChatbotApp
from utils.logger import setup_logger
from core.app_setup import create_application
from utils.window_utils import (
    save_window_state,
    restore_window_state,
)


def main():
    """Initialize and start the application."""
    setup_logger()

    app = create_application()
    window = ChatbotApp()

    # Restore window geometry and state
    restore_window_state(window)

    window.show()

    # Save window state on close and ensure proper cleanup
    def cleanup_and_save():
        save_window_state(window)
        # Ensure all workers are cleaned up before exit
        if hasattr(window, "_cleanup_all_workers"):
            window._cleanup_all_workers()

    app.aboutToQuit.connect(cleanup_and_save)

    try:
        sys.exit(app.exec_())
    except SystemExit:
        # Ensure cleanup even on system exit
        cleanup_and_save()
        raise


if __name__ == "__main__":
    main()
