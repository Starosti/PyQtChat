"""
Window State Management Module

This module provides functions to save and restore the main window's
geometry and state using QSettings.
"""

import logging
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMessageBox

ORGANIZATION_NAME = "PyQtChat"
APPLICATION_NAME = "Starosti"


def save_window_state(window):
    """
    Saves the window's geometry and state.

    Args:
        window: The QMainWindow instance whose state is to be saved.
    """
    try:
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        settings.setValue("geometry", window.saveGeometry())
        settings.setValue("windowState", window.saveState())
    except Exception as e:
        logging.error(f"Failed to save window state: {e}")
        # Don't show popup for window state save failures as they're not critical


def restore_window_state(window):
    """
    Restores the window's geometry and state.

    Args:
        window: The QMainWindow instance whose state is to be restored.
    """
    try:
        settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        geometry = settings.value("geometry")
        if geometry is not None:
            success = window.restoreGeometry(geometry)
            if not success:
                logging.warning("Failed to restore window geometry, using default size")

        window_state = settings.value("windowState")
        if window_state is not None:
            success = window.restoreState(window_state)
            if not success:
                logging.warning("Failed to restore window state, using default layout")
    except Exception as e:
        logging.error(f"Failed to restore window state: {e}")
        # Don't show popup for window state restore failures as they're not critical
