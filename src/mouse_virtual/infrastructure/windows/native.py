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

