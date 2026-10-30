import pytest
from types import SimpleNamespace
from mouse_virtual.modules.agent_control.permissions import DesktopScope
from mouse_virtual.infrastructure.windows.accessibility import AccessibilitySession

def test_desktop_scope_authorization_identity():
    info={"valid":True,"minimized":False,"pid":44,"class":"QtTest"}
    scope=DesktopScope.authorize(1234,info)
    scope.check(1234,info)
    for bad in ({**info,"pid":45},{**info,"minimized":True},{**info,"class":"Other"}):
        with pytest.raises(PermissionError):scope.check(1234,bad)
    with pytest.raises(PermissionError):scope.check(5678,info)

def test_password_edit_rejected_without_reading_value():
    class Sensitive:
        element_info=SimpleNamespace(is_password=True,automation_id="password")
        def is_enabled(self):return True
        def window_text(self):return "secret"
    class Root:
        def descendants(self,**kw):return [Sensitive()]
    a=AccessibilitySession(123)
    a.root=Root()
    with pytest.raises(PermissionError):a.fill("do-not-log",auto_id="password")
    with pytest.raises(PermissionError):a.read(auto_id="password",control_type="Edit")

def test_inspection_omits_protected_elements_and_edit_values():
    class Item:
        def __init__(self,name,typ,protected):
            self.element_info=SimpleNamespace(is_password=protected,automation_id=name,control_type=typ)
        def window_text(self):return "hidden value"
    class Root:
        def descendants(self):return [Item("secret","Edit",True),Item("search","Edit",False)]
    a=AccessibilitySession(123);a.root=Root()
    assert a.inspect()==[{"id":"search","type":"Edit","name":""}]
