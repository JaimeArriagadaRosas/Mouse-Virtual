from PySide6.QtWidgets import QApplication
from mouse_virtual.app.main_window import Main
from mouse_virtual.modules.playback import controller
from mouse_virtual.modules.clicker.scheduler import ClickBudget,ScheduleMetrics

def setup_gui():
    app=QApplication.instance() or QApplication([])
    w=Main()
    w.show_page(0)
    w.mode_combo.setCurrentIndex(0)
    w.target_combo.addItem("Laboratorio",12345)
    w.target_combo.setCurrentIndex(w.target_combo.count()-1)
    w.repeat_count.setValue(5)
    w.repeats[1].setChecked(True)
    w.repeats[0].setChecked(False)
    w.clicktypes[1].setChecked(True)
    w.clicktypes[0].setChecked(False)
    w.positions[2].setChecked(True)
    w.positions[0].setChecked(False)
    w.positions[1].setChecked(False)
    return w

def test_simulated_double_click_odd_limit_does_not_call_os(monkeypatch):
    w=setup_gui()
    try:
        monkeypatch.setattr(controller,"post_click",lambda *a:(_ for _ in ()).throw(AssertionError("Win32 unexpectedly called")))
        monkeypatch.setattr(controller,"native_click",lambda *a,**k:(_ for _ in ()).throw(AssertionError("Global input unexpectedly called")))
        monkeypatch.setattr(controller,"client_size",lambda hwnd:(640,480))
        w.start()
        assert w.running
        w.timer.stop()
        for _ in range(3):w.tick()
        assert w.sent==5
        assert not w.running
        assert w.click_budget.exhausted
    finally:w.stop();w.close()

def test_real_clicker_budget_allocates_partial_double(monkeypatch):
    w=setup_gui()
    try:
        w.mode_combo.setCurrentIndex(1)
        calls=[]
        monkeypatch.setattr(controller,"post_click",lambda hwnd,x,y,button,count:calls.append(count))
        monkeypatch.setattr(controller,"client_size",lambda hwnd:(640,480))
        w.start()
        assert w.running
        w.timer.stop()
        for _ in range(3):w.tick()
        assert calls==[2,2,1]
        assert w.sent==5 and not w.running
    finally:w.stop();w.close()
