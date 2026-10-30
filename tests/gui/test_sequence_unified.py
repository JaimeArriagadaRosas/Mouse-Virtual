from PySide6.QtWidgets import QApplication
from mouse_virtual.app.main_window import Main
from mouse_virtual.modules.sequences.models import Plan,Step
from mouse_virtual.modules.playback import controller as playback_controller

def test_editor_sequence_uses_common_engine(monkeypatch):
    app=QApplication.instance() or QApplication([])
    w=Main()
    try:
        w.show_page(2)
        w.mode_combo.setCurrentIndex(0)
        w.target_combo.addItem("Receptor de laboratorio",12345)
        w.target_combo.setCurrentIndex(w.target_combo.count()-1)
        monkeypatch.setattr(playback_controller,"snapshot",lambda hwnd:{"client_width":640,"client_height":480,"monitors":[]})
        monkeypatch.setattr(playback_controller,"window_info",lambda hwnd:{"pid":200})
        calls=[]
        monkeypatch.setattr(w.playback,"start",lambda *a,**kw:calls.append((a,kw)))
        monkeypatch.setattr(w,"current_plan",lambda:Plan([Step("click",12,18,"middle",0)],1))
        w.start()
        assert len(calls)==1
        assert calls[0][1]["mode"]=="simulation"
        assert w.running
    finally:
        w.stop()
        w.close()

def test_missing_target_never_starts_sequence(monkeypatch):
    app=QApplication.instance() or QApplication([])
    w=Main()
    try:
        w.mode_combo.setCurrentIndex(0)
        w.target_combo.clear()
        calls=[]
        messages=[]
        monkeypatch.setattr(w.playback,"start",lambda *a,**kw:calls.append((a,kw)))
        monkeypatch.setattr(w,"report_error",lambda msg:messages.append(str(msg)))
        w._begin_sequence(Plan([Step("click",3,4)],1))
        assert not calls and not w.running
        assert messages
    finally:w.close()
