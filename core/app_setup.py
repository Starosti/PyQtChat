"""
Application Setup Module

This module handles the initialization and configuration of the QApplication.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import logging
import os


def create_application():
    """
    Initializes and configures the QApplication instance.

    Returns:
        QApplication: The configured application instance.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("PyQtChat")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Starosti")

    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        app.setWindowIcon(QIcon(os.path.join(base_dir, "resources", "icon.ico")))
    except Exception as e:
        logging.warning(f"Warning: Could not load application icon. Error: {e}")
    return app
