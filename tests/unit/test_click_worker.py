import threading,time
from mouse_virtual.modules.clicker.worker import ClickWorker

def test_worker_exact_finite_budget_and_background_dispatch():
    calls=[];completed=[]
    w=ClickWorker(50,5,2,lambda n:(calls.append((n,threading.current_thread().name)) or {"status":"SIMULATED"}),on_end=lambda *a:completed.append(a))
    w.start();w.join(2)
    assert not w.active
    assert [n for n,_ in calls]==[2,2,1]
    assert all(name=="mouse-virtual-clicker" for _,name in calls)
    assert completed and completed[0][0]=="completed" and completed[0][1]==5

def test_worker_cancel_interrupts_wait_without_input():
    calls=[];ended=[]
    w=ClickWorker(500,0 if False else None,1,lambda n:calls.append(n),on_end=lambda *a:ended.append(a))
    w.start()
    started=time.monotonic()
    w.stop();w.join(1)
    assert not w.active
    assert not calls
    assert ended and ended[0][0]=="cancelled"
    assert time.monotonic()-started<.5

def test_worker_dispatch_error_stops_and_reports():
    ended=[]
    def failing(count):raise RuntimeError("test failure")
    w=ClickWorker(50,None,1,failing,on_end=lambda *a:ended.append(a))
    w.start();w.join(1)
    assert ended and ended[0][0]=="error:test failure"
    assert ended[0][1]==0
