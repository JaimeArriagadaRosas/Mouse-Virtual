"""Prevents known background Chromium UIA calls from stealing foreground focus."""
import pytest
from mouse_virtual.infrastructure.windows.accessibility import AccessibilitySession


def test_chrome_background_invoke_is_refused(monkeypatch):
    from mouse_virtual.modules.recording import recorder
    monkeypatch.setattr(recorder, "window_info",
                        lambda hwnd: {"class": "Chrome_WidgetWin_1", "valid": True})
    monkeypatch.setattr(recorder, "active_window", lambda: 999)
    session = AccessibilitySession(123)
    session.find = lambda **kwargs: pytest.fail("Must reject before locating control")
    with pytest.raises(PermissionError, match="steal focus"):
        session.invoke(auto_id="view_1003")


def test_non_browser_uia_invoke_retains_previous_behavior(monkeypatch):
    from mouse_virtual.modules.recording import recorder
    monkeypatch.setattr(recorder, "window_info", lambda hwnd: {"class": "Notepad"})
    monkeypatch.setattr(recorder, "active_window", lambda: 999)
    class Invoker:
        def Invoke(self):
            return None
    class Control:
        def is_enabled(self):
            return True
        @property
        def element_info(self):
            class Info:
                is_password = False
            return Info()
        iface_invoke = Invoker()
    session = AccessibilitySession(123)
    session.find = lambda **kwargs: Control()
    assert session.invoke(auto_id="push")["invoked"]
