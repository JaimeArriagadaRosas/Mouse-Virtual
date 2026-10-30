import pytest
from mouse_virtual.infrastructure.windows.focus_guard import ForegroundGuard

@pytest.mark.parametrize("foreground,valid,minimized,pid",[
    (22,True,False,7),(11,False,False,7),(11,True,True,7),(11,True,False,9)
])
def test_reject_incorrect_or_invalid_window(foreground,valid,minimized,pid):
    guard=ForegroundGuard(11,7,lambda:foreground,lambda _:{"valid":valid,"minimized":minimized,"pid":pid})
    with pytest.raises(RuntimeError):guard.require_target()

def test_accept_exact_hwnd_and_pid():
    guard=ForegroundGuard(11,7,lambda:11,lambda _:{"valid":True,"minimized":False,"pid":7})
    guard.require_target()
