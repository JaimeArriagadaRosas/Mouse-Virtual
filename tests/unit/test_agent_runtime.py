import pytest
from mouse_virtual.modules.agent_control.runtime import validate_request,execute_request

def info(hwnd):
    return {"valid":True,"minimized":False,"pid":12,"class":"TestApp"}
class FakeSession:
    def inspect(self):return [{"id":"query","type":"Edit","name":""}]
class FakeDesktop:
    def __init__(self,hwnd):self.session=FakeSession();self.hwnd=hwnd
    def execute(self,cmd):
        if cmd.action=="desktop.fill":return {"filled":True,"verified":True,"length":len(cmd.text)}
        if cmd.action=="desktop.invoke":return {"invoked":True}
        if cmd.action=="desktop.read_control":return {"text":"Resultados de perritos"}
        return {"found":True,"name":"Search"}

def test_explicit_approval_and_strict_plan():
    base={"mode":"run","hwnd":100,"authorize_hwnd":100}
    with pytest.raises(PermissionError):validate_request({**base,"authorize_hwnd":101,"steps":[]})
    with pytest.raises(ValueError):validate_request({**base,"steps":[{"action":"shell.exec","auto_id":"x"}]})
    with pytest.raises(ValueError):validate_request({**base,"steps":[{"action":"desktop.fill","auto_id":"x","unexpected":"y"}]})

def test_multiple_actions_and_redacted_fill():
    req={"mode":"run","hwnd":100,"authorize_hwnd":100,"steps":[
        {"action":"desktop.fill","auto_id":"query","text":"perritos"},
        {"action":"desktop.invoke","auto_id":"submit","control_type":"Button"},
        {"action":"desktop.read_control","auto_id":"result","control_type":"Text"}]}
    result=execute_request(req,info_provider=info,desktop_factory=FakeDesktop)
    assert result["completed"]==3
    assert result["results"][0]["result"]["verified"]
    assert "perritos" not in str(result["results"][0])
    assert result["results"][2]["result"]["text"]=="Resultados de perritos"

def test_scope_is_rechecked_for_each_step():
    count=[0]
    def changing(hwnd):
        count[0]+=1
        if count[0]>3:return {**info(hwnd),"pid":42}
        return info(hwnd)
    req={"mode":"run","hwnd":100,"authorize_hwnd":100,"steps":[
        {"action":"desktop.fill","auto_id":"query","text":"x"},
        {"action":"desktop.invoke","auto_id":"submit","control_type":"Button"}]}
    with pytest.raises(PermissionError):execute_request(req,info_provider=changing,desktop_factory=FakeDesktop)

def test_inspect():
    result=execute_request({"mode":"inspect","hwnd":100,"authorize_hwnd":100},info_provider=info,desktop_factory=FakeDesktop)
    assert result["controls"][0]["id"]=="query"
