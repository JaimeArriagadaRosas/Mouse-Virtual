"""Independent Windows input adapters. Explicit GLOBAL mode uses physical input;
BACKGROUND mode sends targeted Win32 messages without moving the real pointer."""
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
H=wintypes.HWND
CB=ctypes.WINFUNCTYPE(wintypes.BOOL,H,wintypes.LPARAM)
for fn, argtypes, restype in [
    ("IsWindow",[H],wintypes.BOOL),
    ("IsWindowVisible",[H],wintypes.BOOL),
    ("GetClientRect",[H,ctypes.POINTER(wintypes.RECT)],wintypes.BOOL),
    ("ClientToScreen",[H,ctypes.POINTER(wintypes.POINT)],wintypes.BOOL),
    ("PostMessageW",[H,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM],wintypes.BOOL),
    ("GetWindowTextLengthW",[H],ctypes.c_int),
    ("GetWindowTextW",[H,wintypes.LPWSTR,ctypes.c_int],ctypes.c_int),
    ("EnumWindows",[CB,wintypes.LPARAM],wintypes.BOOL),
    ("EnumChildWindows",[H,CB,wintypes.LPARAM],wintypes.BOOL),
    ("GetClassNameW",[H,wintypes.LPWSTR,ctypes.c_int],ctypes.c_int),
    ("GetCursorPos",[ctypes.POINTER(wintypes.POINT)],wintypes.BOOL),
    ("SetCursorPos",[ctypes.c_int,ctypes.c_int],wintypes.BOOL),
]:
    f=getattr(user32,fn);f.argtypes=argtypes;f.restype=restype

WM_DOWN={"left":0x0201,"right":0x0204,"middle":0x0207}
WM_UP={"left":0x0202,"right":0x0205,"middle":0x0208}
MK={"left":0x1,"right":0x2,"middle":0x10}
INPUT_MOUSE,INPUT_KEYBOARD=0,1
KEYEVENTF_KEYUP=0x0002
MOUSE_FLAGS={"left":(0x0002,0x0004),"right":(0x0008,0x0010),"middle":(0x0020,0x0040)}
ULONG_PTR=wintypes.WPARAM

class MOUSEINPUT(ctypes.Structure):
    _fields_=[("dx",wintypes.LONG),("dy",wintypes.LONG),
              ("mouseData",wintypes.DWORD),("dwFlags",wintypes.DWORD),
              ("time",wintypes.DWORD),("dwExtraInfo",ULONG_PTR)]
class KEYBDINPUT(ctypes.Structure):
    _fields_=[("wVk",wintypes.WORD),("wScan",wintypes.WORD),
              ("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),
              ("dwExtraInfo",ULONG_PTR)]
class HARDWAREINPUT(ctypes.Structure):
    _fields_=[("uMsg",wintypes.DWORD),("wParamL",wintypes.WORD),
              ("wParamH",wintypes.WORD)]
class INPUT_UNION(ctypes.Union):
    _fields_=[("mi",MOUSEINPUT),("ki",KEYBDINPUT),("hi",HARDWAREINPUT)]
class INPUT(ctypes.Structure):
    _fields_=[("type",wintypes.DWORD),("data",INPUT_UNION)]
user32.SendInput.argtypes=[wintypes.UINT,ctypes.POINTER(INPUT),ctypes.c_int]
user32.SendInput.restype=wintypes.UINT

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
