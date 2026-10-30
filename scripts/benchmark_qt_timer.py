"""Qt timer performance diagnosis; NEVER sends mouse or keyboard events."""
import argparse,json,statistics,time
from PySide6.QtCore import QCoreApplication,QTimer
def measure(interval_ms,iterations):
    app=QCoreApplication.instance() or QCoreApplication([])
    samples=[]
    last=time.perf_counter_ns()
    timer=QTimer()
    timer.setTimerType(__import__('PySide6.QtCore',fromlist=['Qt']).Qt.TimerType.PreciseTimer)
    def tick():
        nonlocal last
        now=time.perf_counter_ns();samples.append((now-last)/1e6);last=now
        if len(samples)>=iterations:timer.stop();app.quit()
    timer.timeout.connect(tick)
    timer.start(interval_ms)
    app.exec()
    ordered=sorted(samples)
    return {"requested_ms":interval_ms,"samples":len(samples),"observed_mean_ms":round(statistics.mean(samples),4),"observed_p50_ms":round(ordered[int((len(ordered)-1)*.5)],4),"observed_p95_ms":round(ordered[int((len(ordered)-1)*.95)],4),"observed_p99_ms":round(ordered[int((len(ordered)-1)*.99)],4),"observed_min_ms":round(min(samples),4),"observed_max_ms":round(max(samples),4),"note":"Qt timer events only, no mouse input"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--intervals",type=int,nargs="+",default=[1,5,10,50]);p.add_argument("--count",type=int,default=100)
    a=p.parse_args();print(json.dumps([measure(ms,a.count) for ms in a.intervals],ensure_ascii=False,indent=2))
