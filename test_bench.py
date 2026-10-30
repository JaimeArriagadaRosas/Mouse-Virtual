"""Prueba de recepción de eventos Win32 contra ventana propia; cursor es diagnóstico."""
import sys,ctypes
from ctypes import wintypes
from PySide6.QtCore import QTimer,Qt
from PySide6.QtWidgets import QApplication,QWidget,QLabel,QVBoxLayout
from win32_core import post_click
class Target(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Virtual - Banco de pruebas")
        self.setFixedSize(320,180)
        self.clicks=0
        layout=QVBoxLayout(self)
        self.label=QLabel("Clics recibidos: 0")
        layout.addWidget(self.label)
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.clicks+=1
            self.label.setText(f"Clics recibidos: {self.clicks}")
        super().mousePressEvent(event)
app=QApplication(sys.argv)
w=Target();w.show()
hwnd=int(w.winId())
before=wintypes.POINT()
ctypes.windll.user32.GetCursorPos(ctypes.byref(before))
def run():
    for _ in range(25):
        post_click(hwnd,100,90)
    QTimer.singleShot(350,finish)
def finish():
    after=wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(after))
    print(f"RESULT received={w.clicks} sent=25 cursor_before=({before.x},{before.y}) cursor_after=({after.x},{after.y})",flush=True)
    print("Cursor movement can be physical user activity; motor never calls SetCursorPos/SendInput.",flush=True)
    app.exit(0 if w.clicks==25 else 2)
QTimer.singleShot(300,run)
QTimer.singleShot(5000,lambda:app.exit(3))
sys.exit(app.exec())
