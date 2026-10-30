"""Cancelable, monotonic worker for click operations; no Qt widget calls."""
import threading,time
from .scheduler import ClickBudget,ScheduleMetrics

class ClickWorker:
    def __init__(self,interval_ms,limit,group_size,dispatch,on_progress=None,on_end=None):
        if group_size not in (1,2):raise ValueError("Group size must be 1 or 2")
        self.budget=ClickBudget(interval_ms,limit)
        self.metrics=ScheduleMetrics(interval_ms)
        self.group_size=group_size
        self.dispatch=dispatch
        self.on_progress=on_progress or (lambda *args:None)
        self.on_end=on_end or (lambda *args:None)
        self.cancel=threading.Event()
        self.thread=None
    @property
    def active(self):
        return bool(self.thread and self.thread.is_alive())
    def start(self):
        if self.active:raise RuntimeError("Worker already running")
        self.cancel.clear()
        self.thread=threading.Thread(target=self._run,daemon=True,name="mouse-virtual-clicker")
        self.thread.start()
    def stop(self):
        self.cancel.set()
    def join(self,timeout=None):
        if self.thread:self.thread.join(timeout)
    def _run(self):
        reason="completed"
        interval_ns=self.budget.interval_ms*1_000_000
        self.metrics.start()
        deadline=time.perf_counter_ns()+interval_ns
        try:
            while not self.cancel.is_set() and not self.budget.exhausted:
                delay=max(0,(deadline-time.perf_counter_ns())/1e9)
                if self.cancel.wait(delay):
                    reason="cancelled"
                    break
                if self.cancel.is_set():
                    reason="cancelled"
                    break
                self.metrics.observe()
                count=self.budget.allocate(self.group_size)
                if not count:break
                metadata=self.dispatch(count)
                self.budget.record(count)
                try:self.on_progress(self.budget.emitted,metadata)
                except Exception:pass
                deadline+=interval_ns
                now=time.perf_counter_ns()
                if deadline<now:deadline=now+interval_ns
            if self.cancel.is_set():reason="cancelled"
        except Exception as exc:
            reason="error:"+str(exc)
        finally:
            try:self.on_end(reason,self.budget.emitted,self.metrics.summary())
            except Exception:pass
