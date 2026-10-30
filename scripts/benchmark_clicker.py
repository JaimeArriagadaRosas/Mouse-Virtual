"""Deterministic click-plan dispatcher benchmark; no OS input is produced."""
import argparse,json,time,statistics,tracemalloc
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from mouse_virtual.modules.sequences.models import Plan,Step
def run(n):
    if n not in (100,1000,10000):raise ValueError("Supported sizes: 100, 1000, 10000")
    clicks=0;times=[]
    plan=Plan([Step("click",20,20,"left",0)],1)
    plan.validate()
    tracemalloc.start()
    started=time.perf_counter_ns()
    last=started
    for _ in range(n):
        for step in plan.steps:
            step.validate()
            clicks+=1
        now=time.perf_counter_ns()
        times.append((now-last)/1e6);last=now
    elapsed=(time.perf_counter_ns()-started)/1e9
    current,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    seq=sorted(times)
    return {"mode":"SIMULATED_NO_OS_INPUT","requested":n,"completed":clicks,"elapsed_s":round(elapsed,5),"throughput_ops_per_s":round(clicks/elapsed,1),"gap_p50_ms":round(seq[int((len(seq)-1)*0.5)],5),"gap_p95_ms":round(seq[int((len(seq)-1)*0.95)],5),"gap_p99_ms":round(seq[int((len(seq)-1)*0.99)],5),"peak_allocated_bytes":peak}
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--counts",nargs="+",type=int,default=[100,1000,10000])
    a=parser.parse_args();print(json.dumps([run(n) for n in a.counts],indent=2))
if __name__=="__main__":main()
