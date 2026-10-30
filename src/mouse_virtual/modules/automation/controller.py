"""Mouse Virtual desktop module."""
from mouse_virtual.infrastructure.windows.handles import client_size, windows
from mouse_virtual.modules.automation.view import setup_automation_page
from mouse_virtual.modules.recording.recorder import active_window, window_info

class AutomationMixin:
    def automation_page(self):
        return setup_automation_page(self)

    def populate_windows(self):
        previous=self.target_combo.currentData() if hasattr(self,"target_combo") else None
        self.target_combo.clear()
        for hwnd,title in windows():
            if "Mouse Virtual" not in title:self.target_combo.addItem(title,hwnd)
        pos=self.target_combo.findData(previous)
        if pos>=0:self.target_combo.setCurrentIndex(pos)
        self.update_target_info()

    def bind_foreground(self):
        hwnd=active_window()
        if not hwnd:return
        current=self.target_combo.findData(hwnd)
        if current<0:
            self.populate_windows()
            current=self.target_combo.findData(hwnd)
        if current>=0:self.target_combo.setCurrentIndex(current)
        else:self.report_error('La ventana activa no está disponible para selección.')

    def update_target_info(self):
        hwnd=self.target_combo.currentData()
        if hwnd:
            w,h=client_size(hwnd)
            info=window_info(hwnd)
            self.target_info.setText(f"PID: {info['pid']} · Cliente: {w} × {h} · Minimizada: {info['minimized']}")
            self.target_combo.setToolTip(self.target_info.text()+f" · Clase: {info['class']} · Exterior: {info['outer']}")

