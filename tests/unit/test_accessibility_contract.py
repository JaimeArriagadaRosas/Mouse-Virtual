import pytest
from mouse_virtual.infrastructure.windows.accessibility import AccessibilitySession

class FakeValue:
    def __init__(self):self.CurrentValue=""
    def SetValue(self,value):self.CurrentValue=value
class FakeControl:
    def __init__(self,enabled=True):
        from types import SimpleNamespace
        self.iface_value=FakeValue();self.enabled=enabled
        self.element_info=SimpleNamespace(automation_id="search")
    def is_enabled(self):return self.enabled
    def window_text(self):return ""
class FakeRoot:
    def __init__(self,controls):self.controls=controls
    def descendants(self,**kwargs):return self.controls

def test_target_scope_and_unique_control():
    with pytest.raises(ValueError):AccessibilitySession(0)
    s=AccessibilitySession(111)
    s.root=FakeRoot([FakeControl()])
    result=s.fill("perritos",auto_id="search")
    assert result=={"filled":True,"length":8,"verified":True}

def test_ambiguous_control_is_rejected():
    s=AccessibilitySession(111)
    s.root=FakeRoot([FakeControl(),FakeControl()])
    with pytest.raises(LookupError):s.fill("perritos",name="Buscar")

def test_disabled_control_is_rejected():
    s=AccessibilitySession(111)
    s.root=FakeRoot([FakeControl(False)])
    with pytest.raises(PermissionError):s.fill("perritos",auto_id="search")
