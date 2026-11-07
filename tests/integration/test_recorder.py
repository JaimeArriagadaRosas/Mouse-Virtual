import sys,time,os
import pytest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from mouse_virtual.modules.recording.recorder import MouseRecorder,window_info
from PySide6.QtWidgets import QApplication,QWidget

def test_window_info_invalid():
    info=window_info(0)
    assert info["valid"] is False
    assert info["client"]==[0,0]

@pytest.mark.skipif(os.environ.get("QT_QPA_PLATFORM")=="offscreen",
                    reason="Windows recorder needs a real HWND; offscreen Qt returns a dummy ID")
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
