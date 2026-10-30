"""CLI-only scoped desktop agent runtime; runs in a disposable child process."""
from __future__ import annotations

import time
from mouse_virtual.modules.agent_control.commands import Command
from mouse_virtual.modules.agent_control.desktop import DesktopExecutor
from mouse_virtual.modules.agent_control.executor import AgentExecutor
from mouse_virtual.modules.agent_control.permissions import DesktopScope
from mouse_virtual.modules.recording.recorder import window_info

ACTIONS={"desktop.find_control","desktop.fill","desktop.invoke","desktop.read_control","desktop.wait_text"}
MAX_STEPS=20

def _identifier(value):
    if not isinstance(value,str) or not value or len(value)>200:
        raise ValueError("Explicit nonempty AutomationId required")
    return value

def validate_request(request):
    if not isinstance(request,dict):raise ValueError("Expected JSON object")
    hwnd=request.get("hwnd")
    approved=request.get("authorize_hwnd")
    if type(hwnd) is not int or hwnd<=0 or type(approved) is not int or approved!=hwnd:
        raise PermissionError("Explicit --authorize-hwnd must equal target --hwnd")
    mode=request.get("mode")
    if mode not in ("inspect","run"):raise ValueError("Invalid operation mode")
    steps=request.get("steps",[])
    if mode=="inspect":
        if steps:raise ValueError("Inspect cannot execute actions")
        return []
    if not isinstance(steps,list) or not (1<=len(steps)<=MAX_STEPS):
        raise ValueError("Plan must contain 1 to 20 actions")
    validated=[]
    for step in steps:
        if not isinstance(step,dict):raise ValueError("Invalid step")
        if set(step)-{"action","auto_id","name","control_type","text"}:
            raise ValueError("Unsupported step field")
        action=step.get("action")
        if action not in ACTIONS:raise ValueError("Action not allowed for desktop runtime")
        auto_id=_identifier(step.get("auto_id"))
        control_type=step.get("control_type","Edit")
        expected={"desktop.fill":"Edit","desktop.invoke":"Button"}
        if action in expected and control_type!=expected[action]:
            raise ValueError("Control type does not match action")
        if control_type not in ("Edit","Button","Text"):
            raise ValueError("Unsupported control type")
        if action in ("desktop.read_control","desktop.wait_text") and control_type not in ("Edit","Text"):
            raise ValueError("Read is permitted only for Text and Edit")
        command=Command(action=action,auto_id=auto_id,control_type=control_type,
                        text=step.get("text",""),name=step.get("name",""))
        command.validate()
        validated.append(command)
    return validated

def execute_request(request, *, info_provider=window_info, desktop_factory=DesktopExecutor):
    commands=validate_request(request)
    hwnd=request["hwnd"]
    scope=DesktopScope.authorize(hwnd,info_provider(hwnd))
    scope.check(hwnd,info_provider(hwnd))
    desktop=desktop_factory(hwnd)
    if request["mode"]=="inspect":
        scope.check(hwnd,info_provider(hwnd))
        return {"ok":True,"hwnd":hwnd,"controls":desktop.session.inspect()}
    executor=AgentExecutor(desktop=desktop)
    results=[]
    for index,command in enumerate(commands):
        scope.check(hwnd,info_provider(hwnd))
        if command.action=="desktop.wait_text":
            if not command.text:
                raise ValueError("wait_text requires expected text")
            deadline=time.monotonic()+3
            verified=False
            while time.monotonic()<deadline:
                scope.check(hwnd,info_provider(hwnd))
                current=executor.execute(Command("desktop.read_control",auto_id=command.auto_id,
                                                 control_type=command.control_type))
                if command.text in current.get("text",""):
                    verified=True
                    break
                time.sleep(.08)
            if not verified:
                raise TimeoutError("Expected text did not appear")
            result={"verified":True}
        else:
            result=executor.execute(command)
        if command.action=="desktop.fill":
            result={"filled":result.get("filled"),"verified":result.get("verified"),"length":result.get("length")}
        if command.action=="desktop.find_control":
            result={"found":result.get("found",False)}
        results.append({"index":index,"action":command.action,"result":result})
    return {"ok":True,"hwnd":hwnd,"completed":len(results),"results":results}
