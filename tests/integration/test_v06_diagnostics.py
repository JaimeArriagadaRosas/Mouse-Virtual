"""Regression: playback diagnostics and infinite cancellation, without touching Roblox."""
import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from mouse_virtual.modules.playback import engine as runtime_v03
from mouse_virtual.modules.sequences.models import Plan, Step
class Logger:
    def __init__(self):self.entries=[]
    def write(self,name,**fields):self.entries.append((name,fields))
def test_playback_visual_event_contract(monkeypatch):
    clicks=[]
    monkeypatch.setattr(runtime_v03,"client_size",lambda hwnd:(800,600))
    monkeypatch.setattr(runtime_v03,"window_info",lambda hwnd:{"valid":True,"client":[800,600],"minimized":False,"pid":13})
    monkeypatch.setattr(runtime_v03,"window_pid",lambda hwnd:13)
    monkeypatch.setattr(runtime_v03,"active_window",lambda:99)
    monkeypatch.setattr(runtime_v03,"post_click",lambda hwnd,x,y,button:clicks.append((hwnd,x,y,button)))
    log=Logger();progress=[];ending=[]
    playback=runtime_v03.Playback(log,lambda *args:progress.append(args),lambda *args:ending.append(args))
    playback.start(Plan([Step("click",35,40,"left",5)],2),77)
    playback.thread.join(2)
    assert clicks==[(77,35,40,"left")]*2
    assert len(progress)==2
    assert progress[0][4]["status"]=="POSTED_UNCONFIRMED"
    assert progress[0][4]["x"]==35
    assert ending[0][0]=="completed"
    assert [k for k,v in log.entries].count("STEP_DISPATCHED")==2
def test_infinite_playback_can_stop(monkeypatch):
    monkeypatch.setattr(runtime_v03,"client_size",lambda hwnd:(400,400))
    monkeypatch.setattr(runtime_v03,"window_info",lambda hwnd:{"valid":True,"client":[400,400],"minimized":False,"pid":11})
    monkeypatch.setattr(runtime_v03,"window_pid",lambda hwnd:11)
    monkeypatch.setattr(runtime_v03,"active_window",lambda:12)
    monkeypatch.setattr(runtime_v03,"post_click",lambda *args:None)
    log=Logger();steps=[];done=[]
    play=runtime_v03.Playback(log,lambda *a:steps.append(a),lambda *a:done.append(a))
    play.start(Plan([Step("click",4,5,"left",25)],0),77)
    time.sleep(.14)
    start=time.monotonic();play.stop();play.thread.join(1)
    assert time.monotonic()-start<.5
    assert not play.active
    assert len(steps)>0
    assert done and done[-1][0]=="cancelled"
def test_recorder_has_counters():
    from mouse_virtual.modules.recording.recorder import MouseRecorder
    r=MouseRecorder()
    assert set(("observed","off_target","injected","captured","paused","overflow")).issubset(r.diagnostics())
