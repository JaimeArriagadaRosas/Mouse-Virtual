import time
from PySide6.QtWidgets import QApplication
from mouse_virtual.app.main_window import Main
from mouse_virtual.modules.playback import controller

def test_clicker_cancel_during_wait_no_win32(monkeypatch):
    app=QApplication.instance() or QApplication([])
    w=Main()
    try:
        w.show_page(0)
        w.mode_combo.setCurrentIndex(0)
        w.target_combo.addItem("Fixture",1234)
        w.target_combo.setCurrentIndex(w.target_combo.count()-1)
        w.seconds.setValue(2)
        w.millis.setValue(0)
        w.positions[2].setChecked(True)
        w.positions[0].setChecked(False)
        w.positions[1].setChecked(False)
        monkeypatch.setattr(controller,"post_click",lambda *a: (_ for _ in ()).throw(AssertionError("Unexpected OS input")))
        w.start()
        assert w.running and w.click_worker.active
        w.stop()
        w.click_worker.join(.5)
        assert not w.click_worker.active
        assert w.sent==0
    finally:
        w.close()

def test_stale_clicker_events_are_ignored(monkeypatch):
    app=QApplication.instance() or QApplication([])
    w=Main()
    try:
        w.show_page(0)
        w.mode_combo.setCurrentIndex(0)
        w.target_combo.addItem("Fixture",1234)
        w.target_combo.setCurrentIndex(w.target_combo.count()-1)
        w.seconds.setValue(1)
        w.millis.setValue(0)
        w.positions[2].setChecked(True)
        w.positions[0].setChecked(False)
        w.positions[1].setChecked(False)
        w.start()
        old_events=w.click_worker_events
        old_token=w.click_worker_token
        w.stop()
        w.click_worker.join(.5)
        old_events.put((old_token,"progress",999,{"status":"SIMULATED","count":999,"x":0,"y":0}))
        w.poll_click_worker()
        assert w.sent==0
    finally:
        w.close()
