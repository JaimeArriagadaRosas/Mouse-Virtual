"""DPI-aware client-space geometry and safe coordinate transformations."""
from __future__ import annotations
import ctypes
from ctypes import wintypes

def display_layout():
    try:
        from PySide6.QtWidgets import QApplication
        app=QApplication.instance()
        if not app:return []
        return [{"name":s.name(),"x":s.geometry().x(),"y":s.geometry().y(),
                 "width":s.geometry().width(),"height":s.geometry().height(),
                 "dpr":s.devicePixelRatio()} for s in app.screens()]
    except Exception:return []

def snapshot(hwnd):
    from mouse_virtual.modules.recording.recorder import window_info
    v=window_info(hwnd)
    return {"client_width":v["client"][0],"client_height":v["client"][1],
            "window_width":v["outer"][0],"window_height":v["outer"][1],
            "monitors":display_layout(),"coordinate_space":"client"}

def transform(x,y,original,current,*,scale=True):
    """Return coordinate in current client area; never silently clamp outside bounds."""
    ow=int(original.get("client_width",0));oh=int(original.get("client_height",0))
    cw=int(current.get("client_width",0));ch=int(current.get("client_height",0))
    if min(ow,oh,cw,ch)<=0:raise ValueError("Geometria de ventana invalida")
    if not (0<=x<ow and 0<=y<oh):
        raise ValueError("Coordenada fuera de la grabacion")
    nx=round(x*cw/ow) if scale else int(x)
    ny=round(y*ch/oh) if scale else int(y)
    if nx>=cw:nx=cw-1
    if ny>=ch:ny=ch-1
    if nx<0 or ny<0 or nx>=cw or ny>=ch:raise ValueError("Resultado fuera del destino")
    return nx,ny

def compare(original,current):
    ow=int(original.get("client_width",0));oh=int(original.get("client_height",0))
    cw=int(current.get("client_width",0));ch=int(current.get("client_height",0))
    if min(ow,oh,cw,ch)<=0:return "invalid"
    if (ow,oh)!=(cw,ch):return "rescaled"
    if original.get("monitors") and original.get("monitors")!=current.get("monitors"):return "monitors_changed"
    return "same"

def legacy_geometry(steps,current):
    """Legacy steps lack recording dimensions; don't invent a scaling baseline."""
    return {"coordinate_space":"client_legacy","client_width":current["client_width"],
            "client_height":current["client_height"],"monitors":[]}
