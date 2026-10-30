"""Foreground-scoped Windows mouse recorder.

Low level hooks observe left/right/middle presses and wheel. Only captures while
the bound application's PID is in the foreground. Never suppresses OS input.
No keyboard text is captured; secure by default.
"""
from __future__ import annotations
import ctypes
import queue
import threading
import time
from ctypes import wintypes

U = ctypes.WinDLL("user32", use_last_error=True)
K = ctypes.WinDLL("kernel32", use_last_error=True)
LRESULT=ctypes.c_ssize_t
ULONG_PTR=wintypes.WPARAM
HOOKPROC=ctypes.WINFUNCTYPE(LRESULT,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM)
class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_=[("pt",wintypes.POINT),("mouseData",wintypes.DWORD),
              ("flags",wintypes.DWORD),("time",wintypes.DWORD),
              ("dwExtraInfo",ULONG_PTR)]
class MSG(ctypes.Structure):
    _fields_=[("hwnd",wintypes.HWND),("message",wintypes.UINT),
             ("wParam",wintypes.WPARAM),("lParam",wintypes.LPARAM),
             ("time",wintypes.DWORD),("pt",wintypes.POINT),
             ("lPrivate",wintypes.DWORD)]
U.SetWindowsHookExW.argtypes=[ctypes.c_int,HOOKPROC,ctypes.c_void_p,wintypes.DWORD]
U.SetWindowsHookExW.restype=ctypes.c_void_p
U.CallNextHookEx.argtypes=[ctypes.c_void_p,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM]
U.CallNextHookEx.restype=LRESULT
U.UnhookWindowsHookEx.argtypes=[ctypes.c_void_p]
U.UnhookWindowsHookEx.restype=wintypes.BOOL
U.GetForegroundWindow.restype=wintypes.HWND
U.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
U.GetWindowThreadProcessId.restype=wintypes.DWORD
U.ScreenToClient.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.POINT)]
U.ScreenToClient.restype=wintypes.BOOL
U.GetClientRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
U.GetClientRect.restype=wintypes.BOOL
U.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
U.GetWindowRect.restype=wintypes.BOOL
U.IsIconic.argtypes=[wintypes.HWND];U.IsIconic.restype=wintypes.BOOL
U.IsWindow.argtypes=[wintypes.HWND];U.IsWindow.restype=wintypes.BOOL
U.GetClassNameW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
U.GetClassNameW.restype=ctypes.c_int
U.PostThreadMessageW.argtypes=[wintypes.DWORD,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
U.PostThreadMessageW.restype=wintypes.BOOL
K.GetCurrentThreadId.restype=wintypes.DWORD
K.GetModuleHandleW.argtypes=[wintypes.LPCWSTR];K.GetModuleHandleW.restype=ctypes.c_void_p

WH_MOUSE_LL=14
WM_QUIT=0x12
EVENTS={0x0201:"left",0x0204:"right",0x0207:"middle"}
WM_WHEEL=0x020A

def window_pid(hwnd:int)->int:
    pid=wintypes.DWORD(0)
    if hwnd:U.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
    return int(pid.value)

def active_window()->int:
    return int(U.GetForegroundWindow() or 0)

def window_info(hwnd:int)->dict:
    client=wintypes.RECT()
    window=wintypes.RECT()
    good=bool(hwnd and U.IsWindow(hwnd))
    has_client=bool(good and U.GetClientRect(hwnd,ctypes.byref(client)))
    has_win=bool(good and U.GetWindowRect(hwnd,ctypes.byref(window)))
    name=ctypes.create_unicode_buffer(120)
    if good:U.GetClassNameW(hwnd,name,120)
    return {"hwnd":hwnd,"pid":window_pid(hwnd),"class":name.value,
            "client":[max(0,client.right-client.left),max(0,client.bottom-client.top)] if has_client else [0,0],
            "outer":[max(0,window.right-window.left),max(0,window.bottom-window.top)] if has_win else [0,0],
            "minimized":bool(good and U.IsIconic(hwnd)),"valid":good}

class MouseRecorder:
    """Threaded hook with explicit start/stop and a bounded event queue."""
    def __init__(self):
        self.events=queue.Queue(maxsize=10000)
        self._thread=None
        self._thread_id=0
        self._running=threading.Event()
        self.paused=threading.Event()
        self._ready=threading.Event()
        self._hook=None
        self._proc=None
        self._pid=0
        self._hwnd=0
        self._start=0
        self._last=0
        self._errors=[]
        self.stats={'observed':0,'off_target':0,'injected':0,'captured':0,'paused':0,'overflow':0}

    @property
    def is_running(self):
        return self._running.is_set()

    def start(self,hwnd:int)->None:
        if self.is_running:raise RuntimeError("Grabación ya iniciada")
        self._pid=window_pid(hwnd)
        if not self._pid:raise ValueError("Ventana destino inválida")
        self._hwnd=hwnd
        self._errors.clear()
        self.stats={k:0 for k in self.stats}
        self._ready.clear()
        while not self.events.empty():
            try:self.events.get_nowait()
            except queue.Empty:break
        self.paused.clear()
        self._start=time.monotonic()
        self._last=self._start
        self._running.set()
        self._thread=threading.Thread(target=self._pump,daemon=True,name="mouse-recorder")
        self._thread.start()
        if not self._ready.wait(timeout=3):
            self.stop()
            raise RuntimeError("No se inicializó el hook de Windows")
        if self._errors:
            error=self._errors[-1]
            self.stop()
            raise RuntimeError(error)

    def _pump(self):
        self._thread_id=int(K.GetCurrentThreadId())
        @HOOKPROC
        def callback(ncode,wparam,lparam):
            if ncode>=0 and self._running.is_set():
                if self.paused.is_set():
                    self.stats['paused']+=1
                    return U.CallNextHookEx(None,ncode,wparam,lparam)
                kind=EVENTS.get(int(wparam))
                if kind or int(wparam)==WM_WHEEL:
                    self.stats['observed']+=1
                    event=ctypes.cast(lparam,ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    # LL injected events are excluded to avoid re-recording playback.
                    if event.flags & 0x01:self.stats['injected']+=1
                    if not (event.flags & 0x01):
                        fg=active_window()
                        if not fg or window_pid(fg)!=self._pid:self.stats['off_target']+=1
                        if fg and window_pid(fg)==self._pid:
                            point=wintypes.POINT(event.pt.x,event.pt.y)
                            # Recording positions relative to the captured foreground window.
                            if U.ScreenToClient(self._hwnd,ctypes.byref(point)):
                                now=time.monotonic()
                                payload={"type":"click" if kind else "wheel",
                                         "button":kind or "wheel",
                                         "x":point.x,"y":point.y,
                                         "delay_ms":max(0,round((now-self._last)*1000)),
                                         "at_ms":round((now-self._start)*1000),
                                         "hwnd":self._hwnd}
                                if not kind:payload["wheel_delta"]=ctypes.c_short(event.mouseData>>16).value
                                try:
                                    self.events.put_nowait(payload)
                                    self.stats['captured']+=1
                                    self._last=now
                                except queue.Full:self.stats['overflow']+=1
            return U.CallNextHookEx(None,ncode,wparam,lparam)
        self._proc=callback
        hook=U.SetWindowsHookExW(WH_MOUSE_LL,callback,K.GetModuleHandleW(None),0)
        if not hook:
            self._errors.append(f"SetWindowsHookExW: {ctypes.get_last_error()}")
            self._running.clear()
            self._ready.set()
            return
        self._hook=hook
        self._ready.set()
        msg=MSG()
        while self._running.is_set():
            res=U.GetMessageW(ctypes.byref(msg),None,0,0)
            if res<=0:break
        U.UnhookWindowsHookEx(hook)
        self._hook=None
        self._running.clear()

    def diagnostics(self):
        return dict(self.stats)
    def set_paused(self,value):
        if value:self.paused.set()
        else:
            self._last=time.monotonic()
            self.paused.clear()
    def poll(self,limit=250)->list[dict]:
        batch=[]
        for _ in range(limit):
            try:batch.append(self.events.get_nowait())
            except queue.Empty:break
        return batch

    def stop(self):
        self._running.clear()
        if self._thread_id:
            U.PostThreadMessageW(self._thread_id,WM_QUIT,0,0)
        if self._thread and self._thread.is_alive() and threading.current_thread()!=self._thread:
            self._thread.join(timeout=2)
        self._thread_id=0

