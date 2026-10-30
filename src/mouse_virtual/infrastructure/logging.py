"""JSONL session logs stored outside the source tree."""
import json,threading,time,uuid
from pathlib import Path

BASE=Path.home()/"AppData"/"Local"/"MouseVirtual"/"logs"

class SessionLog:
    def __init__(self):
        BASE.mkdir(parents=True,exist_ok=True)
        self.path=BASE/f"session_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jsonl"
        self.lock=threading.Lock()
    def write(self,event,**details):
        entry={"wall":time.strftime("%Y-%m-%dT%H:%M:%S"),"mono":time.monotonic(),
               "event":event,**details}
        with self.lock:
            with self.path.open("a",encoding="utf-8") as f:
                f.write(json.dumps(entry,ensure_ascii=False,default=str)+"\n")
