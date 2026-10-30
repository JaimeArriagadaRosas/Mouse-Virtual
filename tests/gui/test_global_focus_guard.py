"""Global input focus diagnostics: all native APIs are mocked."""
from PySide6.QtWidgets import QApplication,QMessageBox
from mouse_virtual.app.main_window import Main
from mouse_virtual.modules.playback import controller

def test_global_clicker_stops_when_focus_changes(monkeypatch):
    app=QApplication.instance() or QApplication([])
    w=Main()
    try:
        w.show_page(0)
        w.mode_combo.setCurrentIndex(2)
        w.target_combo.addItem("Lab target",987654)
        w.target_combo.setCurrentIndex(w.target_combo.count()-1)
        w.repeat_count.setValue(20)
        w.repeats[1].setChecked(True)
        w.repeats[0].setChecked(False)
        focus=[987654]
        monkeypatch.setattr(controller,"window_info",lambda hwnd:{"valid":True,"pid":101})
        monkeypatch.setattr(controller,"window_pid",lambda hwnd:101 if hwnd==987654 else 202)
        monkeypatch.setattr(controller,"active_window",lambda:focus[0])
        monkeypatch.setattr(QMessageBox,"warning",lambda *a,**k:QMessageBox.StandardButton.Yes)
        called=[]
        monkeypatch.setattr(controller,"native_click",lambda *a,**k:called.append(a))
        w.start()
        assert w.running
        focus[0]=123456
        w.click_worker.join(2)
        w.poll_click_worker()
        assert not called
        assert not w.running
        assert w.sent==0
        assert "error" in w.summary.text()
    finally:
        w.stop()
        w.close()

def test_global_clicker_requires_initial_target_foreground(monkeypatch):
    app=QApplication.instance() or QApplication([])
    w=Main()
    try:
        w.show_page(0)
        w.mode_combo.setCurrentIndex(2)
        w.target_combo.addItem("Lab target",987654)
        w.target_combo.setCurrentIndex(w.target_combo.count()-1)
        monkeypatch.setattr(controller,"window_info",lambda hwnd:{"valid":True,"pid":101})
        monkeypatch.setattr(controller,"window_pid",lambda hwnd:101 if hwnd==987654 else 202)
        monkeypatch.setattr(controller,"active_window",lambda:123456)
        monkeypatch.setattr(QMessageBox,"warning",lambda *a,**k:QMessageBox.StandardButton.Yes)
        errors=[]
        monkeypatch.setattr(w,"report_error",lambda msg:errors.append(str(msg)))
        w.start()
        assert errors
        assert not w.running
        assert not getattr(w,"click_worker",None) or not w.click_worker.active
    finally:
        w.stop()
        w.close()
