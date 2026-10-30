"""Launch Mouse Virtual with Qt and packaged resources."""
import sys
from PySide6.QtWidgets import QApplication
from mouse_virtual.app.ui_helpers import HERE
from mouse_virtual.app.main_window import Main

def main():
    app=QApplication(sys.argv)
    app.setStyle("Fusion")
    theme=HERE/"theme.qss"
    if theme.exists():app.setStyleSheet(theme.read_text(encoding="utf-8"))
    window=Main()
    window.show()
    return app.exec()
