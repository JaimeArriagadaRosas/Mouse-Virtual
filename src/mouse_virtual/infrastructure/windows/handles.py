"""Win32 HWND discovery and client-coordinate helpers."""
from .native import *

def windows():
    items=[]
    @CB
    def collect(hwnd,_):
        if not user32.IsWindowVisible(hwnd):return True
        n=user32.GetWindowTextLengthW(hwnd)
        if n<1:return True
        buf=ctypes.create_unicode_buffer(min(n+1,512))
        user32.GetWindowTextW(hwnd,buf,len(buf))
        if buf.value.strip():items.append((int(hwnd),buf.value[:100]))
        return True
    user32.EnumWindows(collect,0)
    return items

def children(hwnd):
    found=[]
    @CB
    def collect(child,_):
        if not user32.IsWindowVisible(child):return True
        title=ctypes.create_unicode_buffer(100)
        cls=ctypes.create_unicode_buffer(100)
        user32.GetWindowTextW(child,title,100)
        user32.GetClassNameW(child,cls,100)
        found.append((int(child),cls.value,title.value))
        return True
    if user32.IsWindow(hwnd):user32.EnumChildWindows(hwnd,collect,0)
    return found

def client_size(hwnd):
    rect=wintypes.RECT()
    if not user32.GetClientRect(hwnd,ctypes.byref(rect)):return 0,0
    return rect.right-rect.left,rect.bottom-rect.top

def cursor_pos():
    p=wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(p)):raise ctypes.WinError(ctypes.get_last_error())
    return p.x,p.y

def client_to_screen(hwnd,x,y):
    p=wintypes.POINT(x,y)
    if not user32.ClientToScreen(hwnd,ctypes.byref(p)):raise ctypes.WinError(ctypes.get_last_error())
    return p.x,p.y

