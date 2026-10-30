import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from recorder import MouseRecorder,window_info
from PySide6.QtWidgets import QApplication,QWidget

def test_window_info_invalid():
    info=window_info(0)
    assert info["valid"] is False
    assert info["client"]==[0,0]

def test_recorder_lifecycle():
    app=QApplication.instance() or QApplication([])
    win=QWidget()
    win.setWindowTitle("Grabador - prueba")
    win.resize(300,200);win.show();app.processEvents()
    r=MouseRecorder()
    r.start(int(win.winId()))
    assert r.is_running
    r.stop()
    assert not r.is_running
    win.close()
