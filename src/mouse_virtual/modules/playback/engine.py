"""Mouse Virtual: cancellable threaded playback and structured evidence.
POSTED_UNCONFIRMED means Windows accepted messages; it does not prove target action.
"""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import json, threading, time, uuid, itertools
from pathlib import Path
from mouse_virtual.infrastructure.windows.handles import client_size
from mouse_virtual.infrastructure.windows.input import post_click
from mouse_virtual.modules.recording.recorder import active_window, window_info, window_pid
from mouse_virtual.infrastructure.geometry import snapshot,transform,compare
from mouse_virtual.infrastructure.logging import SessionLog




class Playback:
    def __init__(self,log,progress,ended):
        self.log=log;self.progress=progress;self.ended=ended
        self.cancel=threading.Event();self.thread=None
        self.run_id=None
    @property
    def active(self):return bool(self.thread and self.thread.is_alive())
    def start(self,plan,hwnd,*,mode='win32',recording_geometry=None,scale=True):
        if self.active:raise RuntimeError("Ya se está reproduciendo")
        plan.validate()
        snap=window_info(hwnd)
        w,h=snap["client"]
        if w<1 or h<1:raise ValueError(f"Ventana sin área cliente: {w}x{h}")
        self.run_id=uuid.uuid4().hex[:12]
        self.cancel.clear()
        self.mode=mode
        self.recording_geometry=recording_geometry
        self.scale=scale
        self.log.write("TARGET_CHECK",run_id=self.run_id,info=snap,
                       foreground=active_window(),
                       same_pid=window_pid(active_window())==snap["pid"])
        self.thread=threading.Thread(target=self._run,args=(plan,hwnd,self.run_id),
                                     daemon=True,name="mouse-virtual-playback")
        self.thread.start()
    def _run(self,plan,hwnd,run_id):
        completed=0
        started=time.perf_counter()
        total=None if plan.repeat==0 else len(plan.steps)*plan.repeat
        self.log.write("PLAYBACK_START",run_id=run_id,hwnd=hwnd,
                       steps=len(plan.steps),repeats=plan.repeat)
        reason="completed"
        try:
            for repeat in (itertools.count() if plan.repeat==0 else range(plan.repeat)):
                for index,step in enumerate(plan.steps):
                    if self.cancel.wait(step.delay_ms/1000):
                        reason="cancelled";return
                    if self.cancel.is_set():
                        reason="cancelled";return
                    foreground=active_window()
                    target=window_info(hwnd)
                    if not target["valid"] or min(target["client"])<=0:
                        raise RuntimeError("Ventana destino cerrada o sin área cliente")
                    x,y=step.x,step.y
                    current=snapshot(hwnd) if self.recording_geometry else {'client_width':target['client'][0],'client_height':target['client'][1],'monitors':[]}
                    if self.recording_geometry and step.action=='click':
                        x,y=transform(x,y,self.recording_geometry,current,scale=self.scale)
                    if step.action=="click":
                        if self.mode=='win32':
                            post_click(hwnd,x,y,step.button)
                            status='POSTED_UNCONFIRMED'
                        elif self.mode=='simulation':
                            status='SIMULATED'
                        elif self.mode=='global':
                            from mouse_virtual.infrastructure.windows.input import client_to_screen,native_click
                            if window_pid(active_window())!=target['pid']:
                                raise RuntimeError('Modo global requiere destino enfocado')
                            native_click(step.button,point=client_to_screen(hwnd,x,y))
                            status='GLOBAL_INPUT_SENT_UNCONFIRMED'
                        else:raise ValueError('Modo de ejecucion desconocido')
                    else:
                        status="WAIT_COMPLETED"
                    completed+=1
                    elapsed_ms=round((time.perf_counter()-started)*1000,2)
                    meta={"action":step.action,"x":x,"y":y,"recorded_x":step.x,"recorded_y":step.y,
                          "geometry_status":compare(self.recording_geometry,current) if self.recording_geometry else 'legacy',
                          "button":step.button,"hwnd":hwnd,"foreground":foreground,
                          "same_pid":bool(window_pid(foreground)==target["pid"]),
                          "minimized":target["minimized"],"mode":self.mode,"status":status,"elapsed_ms":elapsed_ms}
                    self.log.write("STEP_DISPATCHED",run_id=run_id,repeat=repeat,
                                   index=index,completed=completed,**meta)
                    try:self.progress(completed,total,repeat,index,meta)
                    except Exception as e:self.log.write("CALLBACK_ERROR",run_id=run_id,error=str(e))
        except Exception as e:
            reason=f"error:{e}"
            self.log.write("PLAYBACK_ERROR",run_id=run_id,message=str(e))
        finally:
            self.log.write("PLAYBACK_END",run_id=run_id,reason=reason,
                           completed=completed,total=total)
            try:self.ended(reason,completed)
            except Exception:pass
    def stop(self):
        if self.active:self.log.write("STOP_REQUESTED",run_id=self.run_id)
        self.cancel.set()
