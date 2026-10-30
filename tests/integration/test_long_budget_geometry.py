import time
from mouse_virtual.modules.clicker.worker import ClickWorker
from mouse_virtual.infrastructure.geometry import transform,compare

def test_large_budget_can_cancel_before_first_input():
    sent=[]
    w=ClickWorker(50,10000,1,lambda count:sent.append(count))
    w.start();w.stop();w.join(1)
    assert not w.active and sent==[]
    assert w.budget.emitted==0

def test_geometry_edges_and_missing_baseline():
    old={"client_width":1920,"client_height":1080,"monitors":[]}
    new={"client_width":1280,"client_height":720,"monitors":[]}
    assert transform(0,0,old,new)==(0,0)
    assert transform(1919,1079,old,new)==(1279,719)
    assert compare(old,{"client_width":0,"client_height":720})=="invalid"
    assert transform(100,100,old,old,scale=False)==(100,100)
