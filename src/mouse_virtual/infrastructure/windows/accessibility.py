"""UI Automation with explicit HWND scope and no synthetic keystrokes."""
from __future__ import annotations


class AccessibilitySession:
    def __init__(self, hwnd: int):
        if not isinstance(hwnd, int) or hwnd <= 0:
            raise ValueError("A positive target HWND is required")
        self.hwnd = hwnd
        self.root = None

    def connect(self):
        from pywinauto import Desktop
        from mouse_virtual.modules.recording.recorder import window_info
        info = window_info(self.hwnd)
        if not info.get("valid") or info.get("minimized"):
            raise ValueError("Target window unavailable")
        self.root = Desktop(backend="uia").window(handle=self.hwnd)
        self.root.wait("exists", timeout=5)
        return self

    def find(self, *, auto_id="", name="", control_type="Edit"):
        if self.root is None:
            raise RuntimeError("Connect to a target first")
        if not auto_id and not name:
            raise ValueError("Specify an automation ID or accessible name")
        # pywinauto descendants does not accept auto_id on every backend.
        # Filter by the UIA element metadata after selecting control type.
        candidates=self.root.descendants(control_type=control_type)
        matches=[]
        for candidate in candidates:
            info=getattr(candidate,"element_info",None)
            candidate_id=getattr(info,"automation_id","")
            candidate_name=candidate.window_text()
            if auto_id and candidate_id!=auto_id:
                continue
            if name and candidate_name!=name:
                continue
            matches.append(candidate)
        if len(matches) != 1:
            raise LookupError(f"Expected one matching control, found {len(matches)}")
        return matches[0]

    def fill(self, text: str, *, auto_id="", name=""):
        if not isinstance(text, str) or len(text) > 5000:
            raise ValueError("Invalid text")
        control = self.find(auto_id=auto_id, name=name, control_type="Edit")
        if not control.is_enabled():
            raise PermissionError("Control is disabled")
        if getattr(control.element_info,"is_password",False):
            raise PermissionError("Protected control cannot be accessed")
        try:
            control.iface_value.SetValue(text)
        except (AttributeError, OSError) as exc:
            raise RuntimeError("Control does not support UIA ValuePattern") from exc
        actual = control.iface_value.CurrentValue
        if actual != text:
            raise RuntimeError("Value verification failed")
        return {"filled": True, "length": len(text), "verified": True}


    def invoke(self, *, auto_id="", name=""):
        # Regression guard: invoking an inactive Chromium button via Windows
        # UI Automation activates the browser and steals OS foreground focus.
        # Route this case through the explicitly paired existing-tab connector.
        from mouse_virtual.modules.recording.recorder import active_window, window_info
        info = window_info(self.hwnd)
        if str(info.get("class", "")).startswith(("Chrome_WidgetWin", "MozillaWindowClass")):
            if int(active_window() or 0) != self.hwnd:
                raise PermissionError("Background browser invoke would steal focus; use the existing-tab connector")
        control=self.find(auto_id=auto_id,name=name,control_type="Button")
        if not control.is_enabled():
            raise PermissionError("Control is disabled")
        if getattr(control.element_info,"is_password",False):
            raise PermissionError("Protected control cannot be accessed")
        try:
            control.iface_invoke.Invoke()
        except (AttributeError,OSError) as exc:
            raise RuntimeError("Control does not support UIA InvokePattern") from exc
        return {"invoked":True}

    def read(self, *, auto_id="", name="", control_type="Text"):
        control=self.find(auto_id=auto_id,name=name,control_type=control_type)
        if getattr(control.element_info,"is_password",False):
            raise PermissionError("Protected control cannot be read")
        if control_type=="Edit":
            return {"text":control.iface_value.CurrentValue}
        return {"text":control.window_text()}

    def inspect(self):
        if self.root is None:
            raise RuntimeError("Connect to a target first")
        data=[]
        for item in self.root.descendants():
            info=item.element_info
            if getattr(info,"control_type","") not in ("Edit","Button","Text"):
                continue
            if getattr(info,"is_password",False):
                continue
            auto_id=getattr(info,"automation_id","")
            if not auto_id:continue
            data.append({"id":auto_id,"type":info.control_type,
                         "name":"" if info.control_type=="Edit" else item.window_text()[:100]})
            if len(data)>=100:break
        return data
