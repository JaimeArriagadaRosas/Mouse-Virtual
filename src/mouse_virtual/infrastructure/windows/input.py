"""Targeted and global Windows input adapters."""
from .native import *
from .handles import windows, children, client_size, cursor_pos, client_to_screen

def post_click(hwnd,x,y,button="left",count=1):
    if button not in WM_DOWN:raise ValueError("Botón no reconocido")
    if not user32.IsWindow(hwnd):raise ValueError("La ventana destino ya no existe")
    w,h=client_size(hwnd)
    if not (0<=x<w and 0<=y<h and x<=32767 and y<=32767):
        raise ValueError(f"Coordenadas ({x},{y}) fuera de cliente {w}x{h}")
    lp=((y&65535)<<16)|(x&65535)
    for _ in range(count):
        if not user32.PostMessageW(hwnd,WM_DOWN[button],MK[button],lp):
            raise ctypes.WinError(ctypes.get_last_error())
        if not user32.PostMessageW(hwnd,WM_UP[button],0,lp):
            raise ctypes.WinError(ctypes.get_last_error())
    return count

def _send(items):
    array=(INPUT*len(items))(*items)
    n=user32.SendInput(len(array),array,ctypes.sizeof(INPUT))
    if n!=len(array):raise ctypes.WinError(ctypes.get_last_error())
    return n

def native_click(button="left",count=1,point=None):
    """Physical/global mouse input; moves real pointer only when point is set."""
    if button not in MOUSE_FLAGS:raise ValueError("Botón desconocido")
    if point is not None and not user32.SetCursorPos(int(point[0]),int(point[1])):
        raise ctypes.WinError(ctypes.get_last_error())
    down,up=MOUSE_FLAGS[button]
    for _ in range(count):
        _send([INPUT(type=INPUT_MOUSE,data=INPUT_UNION(mi=MOUSEINPUT(dwFlags=down))),
               INPUT(type=INPUT_MOUSE,data=INPUT_UNION(mi=MOUSEINPUT(dwFlags=up)))])
    return count

VK={"ESPACIO":0x20,"ENTER":0x0D,"TAB":0x09,"ESC":0x1B,
    "ARRIBA":0x26,"ABAJO":0x28,"IZQUIERDA":0x25,"DERECHA":0x27,
    "CTRL":0x11,"ALT":0x12,"SHIFT":0x10,"BACKSPACE":0x08}
VK.update({f"F{i}":0x6F+i for i in range(1,13)})
VK.update({chr(i):i for i in range(ord("A"),ord("Z")+1)})
VK.update({str(i):ord(str(i)) for i in range(10)})

def native_key(key):
    """Global keystrokes go to focused application, not a background target."""
    code=VK.get(key.upper())
    if code is None:raise ValueError(f"Tecla desconocida: {key}")
    _send([INPUT(type=INPUT_KEYBOARD,data=INPUT_UNION(ki=KEYBDINPUT(wVk=code))),
           INPUT(type=INPUT_KEYBOARD,data=INPUT_UNION(ki=KEYBDINPUT(wVk=code,dwFlags=KEYEVENTF_KEYUP)))])
    return True
