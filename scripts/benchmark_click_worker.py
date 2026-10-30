"""Measure live ClickWorker scheduling with a safe simulated dispatch."""
import argparse,json,time,tracemalloc,threading
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from mouse_virtual.modules.clicker.worker import ClickWorker

def bench(count,interval):
    records=[]
    ended=[]
    def dispatch(n):
        records.append((time.perf_counter_ns(),n))
        return {"status":"SIMULATED"}
    tracemalloc.start()
    begin=time.perf_counter()
    worker=ClickWorker(interval,count,1,dispatch,on_end=lambda *args:ended.append(args))
    worker.start()
    worker.join(count*interval/1000+10)
    duration=time.perf_counter()-begin
    current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    if worker.active:
        worker.stop();worker.join(3)
        raise RuntimeError("Worker did not finish")
    gaps=[(records[i][0]-records[i-1][0])/1e6 for i in range(1,len(records))]
    gaps.sort()
    return {"mode":"SIMULATED_NO_OS_INPUT","requested":count,"completed":worker.budget.emitted,
            "interval_ms":interval,"elapsed_s":round(duration,3),"throughput_ops_s":round(count/duration,3),
            "gap_p50_ms":round(gaps[int((len(gaps)-1)*.5)],3) if gaps else None,
            "gap_p95_ms":round(gaps[int((len(gaps)-1)*.95)],3) if gaps else None,
            "gap_p99_ms":round(gaps[int((len(gaps)-1)*.99)],3) if gaps else None,
            "peak_python_alloc_bytes":peak,"reason":ended[0][0] if ended else "missing",
            "drift":ended[0][2] if ended else {}}
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--count",type=int,default=100)
    a.add_argument("--interval",type=int,default=50)
    v=a.parse_args()
    if not 1<=v.count<=10000:raise ValueError("count outside 1..10000")
    print(json.dumps(bench(v.count,v.interval),ensure_ascii=False,indent=2))
