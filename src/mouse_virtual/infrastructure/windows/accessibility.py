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
        params = {"control_type":control_type}
        if auto_id:
            params["auto_id"] = auto_id
        if name:
            params["title"] = name
        matches = self.root.descendants(**params)
        if len(matches) != 1:
            raise LookupError(f"Expected one matching control, found {len(matches)}")
        return matches[0]

    def fill(self, text: str, *, auto_id="", name=""):
        if not isinstance(text, str) or len(text) > 5000:
            raise ValueError("Invalid text")
        control = self.find(auto_id=auto_id, name=name, control_type="Edit")
        if not control.is_enabled():
            raise PermissionError("Control is disabled")
        try:
            control.iface_value.SetValue(text)
        except (AttributeError, OSError) as exc:
            raise RuntimeError("Control does not support UIA ValuePattern") from exc
        actual = control.iface_value.CurrentValue
        if actual != text:
            raise RuntimeError("Value verification failed")
        return {"filled": True, "length": len(text), "verified": True}
