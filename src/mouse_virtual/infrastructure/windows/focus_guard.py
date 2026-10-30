"""Global mouse input guard: never send to a different foreground window."""
from dataclasses import dataclass
from typing import Callable, Mapping, Any


@dataclass(frozen=True)
class ForegroundGuard:
    hwnd: int
    pid: int
    active_window: Callable[[], int]
    window_info: Callable[[int], Mapping[str, Any]]

    def require_target(self) -> None:
        if not self.hwnd or not self.pid:
            raise RuntimeError("Invalid target window or process")
        data = self.window_info(self.hwnd)
        if not data.get("valid", False) or data.get("minimized", False):
            raise RuntimeError("Target window closed or minimized; global input stopped")
        if data.get("pid") != self.pid:
            raise RuntimeError("Target process changed; global input stopped")
        if int(self.active_window() or 0) != int(self.hwnd):
            raise RuntimeError("Target lost exact foreground HWND; global input stopped")
