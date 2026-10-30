"""Explicit per-window authorization and identity verification."""
from dataclasses import dataclass

@dataclass(frozen=True)
class DesktopScope:
    hwnd: int
    pid: int
    window_class: str

    @classmethod
    def authorize(cls, hwnd, info):
        if not isinstance(hwnd,int) or hwnd<=0 or not info.get("valid") or info.get("minimized"):
            raise PermissionError("Ventana destino no disponible")
        if not info.get("pid") or not info.get("class"):
            raise PermissionError("Identidad de ventana incompleta")
        return cls(hwnd,int(info["pid"]),str(info["class"]))

    def check(self, hwnd, info):
        if (hwnd!=self.hwnd or not info.get("valid") or info.get("minimized")
                or info.get("pid")!=self.pid or info.get("class")!=self.window_class):
            raise PermissionError("La ventana autorizada ha cambiado o ya no existe")
