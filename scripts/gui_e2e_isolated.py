"""Full GUI event-loop test in a local sandbox. No real mouse events."""
import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from mouse_virtual.modules.playback import engine as runtime_v03
from mouse_virtual.app.main_window import Main
from mouse_virtual.modules.sequences.models import Plan,Step
from unittest.mock import patch

app=QApplication([])
with patch.object(runtime_v03,'window_info',return_value={'valid':True,'client':[1920,1080],'minimized':False,'pid':99}),\
     patch.object(runtime_v03,'client_size',return_value=(1920,1080)),\
     patch.object(runtime_v03,'snapshot',return_value={'client_width':1920,'client_height':1080,'monitors':[]}),\
     patch.object(runtime_v03,'active_window',return_value=33),\
     patch.object(runtime_v03,'window_pid',return_value=1),\
     patch.object(runtime_v03,'post_click',return_value=1):
    gui=Main()
    gui.show_page(4)
    gui.target=12345
    gui.sent=0
    gui.running=True
    gui.action_mode='sequence'
    gui.start_time=time.monotonic()
    gui.playback.start(Plan([Step('click',100,200,delay_ms=18)],0),12345)
    def inspect():
        gui.refresh_stats()
        assert gui.sent>10,(gui.sent,len(gui.playback_events))
        assert gui.counter.text()==str(gui.sent),gui.counter.text()
        assert '∞' in gui.summary.text(),gui.summary.text()
        gui.stop()
        gui.playback.thread.join(2)
        assert not gui.playback.active
        print('GUI_E2E_OK',gui.sent,gui.counter.text(),gui.summary.text().encode('ascii','backslashreplace').decode(),flush=True)
        gui.close()
        app.quit()
    QTimer.singleShot(650,inspect)
    QTimer.singleShot(3500,app.quit)
    app.exec()
