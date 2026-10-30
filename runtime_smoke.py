import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime_v03 import Playback,SessionLog
from plans import Plan,Step
from PySide6.QtWidgets import QApplication,QWidget
app=QApplication.instance() or QApplication([])
w=QWidget();w.setWindowTitle("Playback test");w.resize(400,300);w.show();app.processEvents()
logs=SessionLog()
progress=[];end=[]
p=Playback(logs,lambda *v:progress.append(v),lambda *v:end.append(v))
p.start(Plan([Step("wait",delay_ms=2000)],100),int(w.winId()))
time.sleep(.12)
started=time.monotonic()
p.stop()
p.thread.join(2)
elapsed=time.monotonic()-started
print("CANCEL",elapsed,"END",end,"ACTIVE",p.active)
assert elapsed<.5 and not p.active
p.start(Plan([Step("click",100,100,delay_ms=30)],5),int(w.winId()))
p.thread.join(3)
print("EXEC",progress,end,"LOG",logs.path)
assert len(progress)==5 and not p.active
w.close()
