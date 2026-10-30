"""Win32 isolated input receiver lab, no window shown, no global mouse injection."""
import ctypes, json, time, threading, os, sys, argparse
from pathlib import Path
from ctypes import wintypes
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from mouse_virtual.infrastructure.windows.input import post_click, client_size, cursor_pos
U=ctypes.WinDLL('user32', use_last_error=True)
K=ctypes.WinDLL('kernel32', use_last_error=True)
LRESULT=ctypes.c_ssize_t
HINSTANCE=wintypes.HINSTANCE
WNDPROC=ctypes.WINFUNCTYPE(LRESULT,wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM)
class WNDCLASSEXW(ctypes.Structure):
    _fields_=[('cbSize',wintypes.UINT),('style',wintypes.UINT),('lpfnWndProc',WNDPROC),
              ('cbClsExtra',ctypes.c_int),('cbWndExtra',ctypes.c_int),('hInstance',HINSTANCE),
              ('hIcon',wintypes.HICON),('hCursor',wintypes.HANDLE),('hbrBackground',wintypes.HBRUSH),
              ('lpszMenuName',wintypes.LPCWSTR),('lpszClassName',wintypes.LPCWSTR),
              ('hIconSm',wintypes.HICON)]
U.DefWindowProcW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
U.DefWindowProcW.restype=LRESULT
U.RegisterClassExW.argtypes=[ctypes.POINTER(WNDCLASSEXW)]
U.RegisterClassExW.restype=wintypes.ATOM
U.CreateWindowExW.argtypes=[wintypes.DWORD,wintypes.LPCWSTR,wintypes.LPCWSTR,
    wintypes.DWORD,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,
    wintypes.HWND,wintypes.HMENU,HINSTANCE,ctypes.c_void_p]
U.CreateWindowExW.restype=wintypes.HWND
U.PeekMessageW.argtypes=[ctypes.c_void_p,wintypes.HWND,wintypes.UINT,wintypes.UINT,wintypes.UINT]
U.PeekMessageW.restype=wintypes.BOOL
U.TranslateMessage.argtypes=[ctypes.c_void_p]
U.DispatchMessageW.argtypes=[ctypes.c_void_p]
U.DestroyWindow.argtypes=[wintypes.HWND]
U.DestroyWindow.restype=wintypes.BOOL
class MSG(ctypes.Structure):
    _fields_=[('hwnd',wintypes.HWND),('message',wintypes.UINT),('wParam',wintypes.WPARAM),
       ('lParam',wintypes.LPARAM),('time',wintypes.DWORD),('pt',wintypes.POINT),
       ('lPrivate',wintypes.DWORD)]
events=[]
@WNDPROC
def wndproc(hwnd,msg,wparam,lparam):
    if msg in (0x201,0x202,0x204,0x205,0x207,0x208):
        x=ctypes.c_short(lparam & 0xffff).value
        y=ctypes.c_short((lparam >> 16) & 0xffff).value
        events.append((int(msg),x,y))
        return 0
    return U.DefWindowProcW(hwnd,msg,wparam,lparam)
classname='MV_Input_Lab_'+str(os.getpid())
wc=WNDCLASSEXW()
wc.cbSize=ctypes.sizeof(wc)
wc.lpfnWndProc=wndproc
wc.lpszClassName=classname
wc.hInstance=K.GetModuleHandleW(None)
atom=U.RegisterClassExW(ctypes.byref(wc))
if not atom:raise ctypes.WinError(ctypes.get_last_error())
hwnd=U.CreateWindowExW(0,classname,'Mouse Virtual internal lab',0,0,0,320,240,None,None,wc.hInstance,None)
if not hwnd:raise ctypes.WinError(ctypes.get_last_error())
parser=argparse.ArgumentParser()
parser.add_argument('--stress-clicks',type=int,default=0)
args=parser.parse_args()
if not 0<=args.stress_clicks<=3000:raise ValueError('Stress clicks allowed from 0 to 3000')
expected_events=18+2*args.stress_clicks
start_pointer=cursor_pos()
errors=[]
try:
    for button in ('left','right','middle'):
        post_click(hwnd,45,55,button,3)
    if args.stress_clicks:post_click(hwnd,45,55,'left',args.stress_clicks)
    started=time.monotonic()
    m=MSG()
    while time.monotonic()-started<3.0:
        while U.PeekMessageW(ctypes.byref(m),None,0,0,1):
            U.TranslateMessage(ctypes.byref(m))
            U.DispatchMessageW(ctypes.byref(m))
        if len(events)>=expected_events:break
        time.sleep(0.005)
    ends=cursor_pos()
    expected=[(0x201,0x202),(0x204,0x205),(0x207,0x208)]
    count_pairs={}
    for down,up in expected:
        count_pairs[str(down)]=[sum(x[0]==down for x in events),sum(x[0]==up for x in events)]
    outcome={
      'receiver':'hidden_window_Win32_test',
      'hwnd':int(hwnd),'client_size':client_size(hwnd),
      'message_count':len(events),'per_button_counts':count_pairs,
      'all_coordinates_match':all(x[1:]==(45,55) for x in events),
      'cursor_unchanged':start_pointer==ends,
      'foreground_window_not_modified':True,
      'events_received':events[:24] if args.stress_clicks else events,
      'stress_clicks':args.stress_clicks,'expected_events':expected_events,
      'passed':len(events)==expected_events and all(x[1:]==(45,55) for x in events) }
    print(json.dumps(outcome,ensure_ascii=False))
finally:
    U.DestroyWindow(hwnd)
