from pathlib import Path
from tempfile import TemporaryDirectory
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from geometry import transform,compare
from sequence_store import SequenceStore
from plans import Step,Plan
import runtime_v03
import pytest
def test_monitor_reconfiguration_and_resize():
    old={'client_width':1920,'client_height':1080,'monitors':[{'name':'left'},{'name':'right'}]}
    new={'client_width':1280,'client_height':720,'monitors':[{'name':'right'}]}
    assert compare(old,new)=='rescaled'
    assert transform(960,540,old,new)==(640,360)
    assert transform(1919,1079,old,new)==(1279,719)
def test_window_move_no_rescale():
    old={'client_width':1280,'client_height':720,'monitors':[1,2]}
    new={'client_width':1280,'client_height':720,'monitors':[2]}
    assert compare(old,new)=='monitors_changed'
    assert transform(220,330,old,new)==(220,330)
def test_outside_coordinates_rejected():
    old={'client_width':100,'client_height':80}
    new={'client_width':200,'client_height':160}
    with pytest.raises(ValueError):transform(100,20,old,new)
    with pytest.raises(ValueError):transform(-1,20,old,new)
def test_sequence_retains_capture_geometry():
    root=Path(__file__).resolve().parents[1]
    with TemporaryDirectory(dir=root) as tmp:
        store=SequenceStore(tmp)
        geom={'client_width':100,'client_height':200,'monitors':[{'x':-1080,'y':0,'width':1080,'height':1920}]}
        seq=store.create([Step('click',10,20)],geometry=geom)
        assert store.get(seq['id'])['geometry']==geom
def test_simulation_never_calls_win32(monkeypatch):
    monkeypatch.setattr(runtime_v03,'window_info',lambda hwnd:{'valid':True,'client':[100,100],'minimized':False,'pid':55})
    monkeypatch.setattr(runtime_v03,'client_size',lambda hwnd:(100,100))
    monkeypatch.setattr(runtime_v03,'active_window',lambda:0)
    monkeypatch.setattr(runtime_v03,'window_pid',lambda hwnd:0)
    monkeypatch.setattr(runtime_v03,'snapshot',lambda hwnd:{'client_width':100,'client_height':100,'monitors':[]})
    calls=[]
    monkeypatch.setattr(runtime_v03,'post_click',lambda *a:calls.append(a))
    class L:
        def write(self,*args,**kwargs):pass
    steps=[];ends=[]
    p=runtime_v03.Playback(L(),lambda *x:steps.append(x),lambda *x:ends.append(x))
    p.start(Plan([Step('click',10,20,'left',1)],2),55,mode='simulation')
    p.thread.join(2)
    assert not calls and len(steps)==2
    assert steps[0][-1]['status']=='SIMULATED'
def test_runtime_rescale_and_log(monkeypatch):
    monkeypatch.setattr(runtime_v03,'window_info',lambda hwnd:{'valid':True,'client':[200,200],'minimized':False,'pid':55})
    monkeypatch.setattr(runtime_v03,'client_size',lambda hwnd:(200,200))
    monkeypatch.setattr(runtime_v03,'active_window',lambda:0)
    monkeypatch.setattr(runtime_v03,'window_pid',lambda hwnd:0)
    monkeypatch.setattr(runtime_v03,'snapshot',lambda hwnd:{'client_width':200,'client_height':200,'monitors':[]})
    calls=[]
    monkeypatch.setattr(runtime_v03,'post_click',lambda *a:calls.append(a))
    class L:
        def write(self,*args,**kwargs):pass
    p=runtime_v03.Playback(L(),lambda *a:None,lambda *a:None)
    p.start(Plan([Step('click',50,50,'left',1)],1),33,mode='win32',recording_geometry={'client_width':100,'client_height':100,'monitors':[]})
    p.thread.join(2)
    assert calls==[(33,100,100,'left')]
