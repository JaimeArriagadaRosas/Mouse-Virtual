import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from main import Main

def test_progress_event_from_thread_reaches_gui(monkeypatch):
    app=QApplication.instance() or QApplication([])
    w=Main()
    try:
        w.target=0
        info={'action':'click','x':28,'y':31,'status':'POSTED_UNCONFIRMED'}
        w.playback_events.append(('progress',(1,None,0,0,info)))
        w.poll_playback()
        assert w.sent==1
        assert '1/∞' in w.summary.text()
        assert 'no confirmado' in w.state.text()
    finally:w.close()

def test_many_progress_events_and_stop(monkeypatch):
    app=QApplication.instance() or QApplication([])
    w=Main()
    try:
        w.target=0
        for i in range(600):
            w.playback_events.append(('progress',(i+1,None,i//37,i%37,{'action':'wait','status':'WAIT_COMPLETED','x':0,'y':0})))
        w.playback_events.append(('ended',('cancelled',600)))
        w.poll_playback()
        w.refresh_stats()
        assert w.sent==600
        assert not w.running
        assert '600' in w.counter.text()
        assert 'cancelled' in w.summary.text()
    finally:w.close()
