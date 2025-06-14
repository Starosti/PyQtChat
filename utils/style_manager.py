"""
Style management utilities for the application.
"""

import os
import logging
from PyQt5.QtCore import QSettings

# Load CodeHilite CSS for HTML rendering
CODE_HILITE_STYLE_LIGHT = ""
CODE_HILITE_STYLE_DARK = ""
CURRENT_CODE_HILITE_STYLE = ""

GLOBAL_STYLESHEET = """
    QSplitter::handle {
        border-radius: 4px;
        margin: 20px 0px;
    }
"""


def check_style_vars():
    global CODE_HILITE_STYLE_LIGHT, CODE_HILITE_STYLE_DARK, CURRENT_CODE_HILITE_STYLE
    if CURRENT_CODE_HILITE_STYLE != "":
        return
    # Load style files
    try:
        import os

        base_dir = os.path.dirname(os.path.dirname(__file__))

        style_light_path = os.path.join(base_dir, "resources", "styles.css")
        style_dark_path = os.path.join(base_dir, "resources", "styles_dark.css")

        # Check if files exist before trying to read them
        if not os.path.exists(style_light_path):
            logging.warning(f"Light theme style file not found at {style_light_path}")
            raise FileNotFoundError(f"Style file not found: {style_light_path}")

        if not os.path.exists(style_dark_path):
            logging.warning(f"Dark theme style file not found at {style_dark_path}")
            raise FileNotFoundError(f"Style file not found: {style_dark_path}")

        with open(style_light_path, encoding="utf-8") as f:
            CODE_HILITE_STYLE_LIGHT = f.read()

        with open(style_dark_path, encoding="utf-8") as f:
            CODE_HILITE_STYLE_DARK = f.read()

        # Default to light style; will be updated in apply_theme
        CURRENT_CODE_HILITE_STYLE = CODE_HILITE_STYLE_LIGHT

    except FileNotFoundError as e:
        logging.error(f"Style files not found: {e}")
        # Provide more comprehensive fallback styles
        CODE_HILITE_STYLE_LIGHT = """
        pre { 
            background-color: #f8f8f8; 
            padding: 12px; 
            border-radius: 4px; 
            border: 1px solid #ddd;
            font-family: 'Consolas', 'Courier New', monospace;
            overflow-x: auto;
        }
        code { 
            background-color: #f0f0f0; 
            padding: 2px 4px; 
            border-radius: 3px; 
            font-family: 'Consolas', 'Courier New', monospace;
        }
        """
        CODE_HILITE_STYLE_DARK = """
        pre { 
            background-color: #2d2d2d; 
            color: #f8f8f2; 
            padding: 12px; 
            border-radius: 4px; 
            border: 1px solid #555;
            font-family: 'Consolas', 'Courier New', monospace;
            overflow-x: auto;
        }
        code { 
            background-color: #3d3d3d; 
            color: #f8f8f2; 
            padding: 2px 4px; 
            border-radius: 3px; 
            font-family: 'Consolas', 'Courier New', monospace;
        }
        """
        CURRENT_CODE_HILITE_STYLE = CODE_HILITE_STYLE_LIGHT
    except PermissionError as e:
        logging.error(f"Permission denied accessing style files: {e}")
        # Use minimal fallback
        CODE_HILITE_STYLE_LIGHT = "pre { background-color: #f5f5f5; padding: 10px; }"
        CODE_HILITE_STYLE_DARK = (
            "pre { background-color: #2d2d2d; color: #f8f8f2; padding: 10px; }"
        )
        CURRENT_CODE_HILITE_STYLE = CODE_HILITE_STYLE_LIGHT
    except Exception as e:
        logging.error(f"Unexpected error loading code highlighting styles: {e}")
        # Provide minimal fallback styles
        CODE_HILITE_STYLE_LIGHT = "pre { background-color: #f5f5f5; padding: 10px; }"
        CODE_HILITE_STYLE_DARK = (
            "pre { background-color: #2d2d2d; color: #f8f8f2; padding: 10px; }"
        )
        CURRENT_CODE_HILITE_STYLE = CODE_HILITE_STYLE_LIGHT


def update_current_style():
    """Update the current code highlighting style based on theme setting."""
    check_style_vars()
    global CURRENT_CODE_HILITE_STYLE
    settings = QSettings("PyQtChat", "Starosti")
    dark_mode = settings.value("dark_mode", False, type=bool)

    CURRENT_CODE_HILITE_STYLE = (
        CODE_HILITE_STYLE_DARK if dark_mode else CODE_HILITE_STYLE_LIGHT
    )
    return CURRENT_CODE_HILITE_STYLE


def get_current_code_style():
    """Get the current code highlighting style."""
    return update_current_style()


def get_app_stylesheet(dark_mode=False):
    """Get the application stylesheet for the current theme."""
    if dark_mode:
        return (
            GLOBAL_STYLESHEET
            + """
        QMainWindow, QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMenuBar {
            background-color: #3c3c3c;
            color: #ffffff;
        }
        QMenuBar::item:selected {
            background-color: #555555;
        }
        QMenu {
            background-color: #3c3c3c;
            color: #ffffff;
        }
        QMenu::item:selected {
            background-color: #555555;
        }
        QLineEdit, QTextEdit, QSpinBox {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
        }
        QPushButton {
            background-color: #555555;
            color: #ffffff;
            border: 1px solid #666666;
            border-radius: 4px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #666666;
        }
        QPushButton:pressed {
            background-color: #444444;
        }
        QComboBox {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            color: #ffffff;
            selection-background-color: #555555;
        }
        QScrollArea {
            background-color: #2b2b2b;
            border: none;
        }
        QScrollBar:vertical {
            background: #3c3c3c;
            width: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #555555;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
            border: none;
        }
        QScrollBar:horizontal {
            background: #3c3c3c;
            height: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background: #555555;
            min-width: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            background: none;
            border: none;
        }
        QSplitter::handle {
            background: #3c3c3c;
        }
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
            border-radius: 4px;
        }
        QTabBar::tab {
            background: #3c3c3c;
            color: #ffffff;
            padding: 8px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border: 1px solid #555555;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background: #555555;
            border-bottom: 1px solid #555555;
        }
        QTabBar::tab:!selected {
            margin-top: 2px;
        }
        """
        )
    else:
        return (
            GLOBAL_STYLESHEET
            + """
        QMainWindow, QWidget {
            background-color: #f0f0f0;
            color: #000000;
        }
        QMenuBar {
            background-color: #e8e8e8;
            color: #000000;
        }
        QMenuBar::item:selected {
            background-color: #dcdcdc;
        }
        QMenu {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
        }
        QMenu::item:selected {
            background-color: #f0f0f0;
        }
        QLineEdit, QTextEdit, QSpinBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px;
        }
        QPushButton {
            background-color: #e0e0e0;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #dcdcdc;
        }
        QPushButton:pressed {
            background-color: #c8c8c8;
        }
        QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #000000;
        }
        QScrollArea {
            background-color: #f0f0f0;
            border: none;
        }
        QScrollBar:vertical {
            background: #e8e8e8;
            width: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #cccccc;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
            border: none;
        }
        QScrollBar:horizontal {
            background: #e8e8e8;
            height: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background: #cccccc;
            min-width: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            background: none;
            border: none;
        }
        QSplitter::handle {
            background: #cccccc;
        }
        QGroupBox {
            border: 1px solid #cccccc;
            border-radius: 4px;
            margin-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            background-color: #f0f0f0;
            color: #000000;
        }
        QLabel {
            color: #000000;
        }
        QTabWidget::pane {
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        QTabBar::tab {
            background: #e8e8e8;
            color: #000000;
            padding: 8px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border: 1px solid #cccccc;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background: #f0f0f0;
            border-bottom: 1px solid #f0f0f0;
        }
        QTabBar::tab:!selected {
            margin-top: 2px;
        }
        """
        )
