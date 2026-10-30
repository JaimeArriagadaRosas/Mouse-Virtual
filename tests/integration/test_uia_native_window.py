import os,subprocess,sys,time
from pathlib import Path
from mouse_virtual.modules.agent_control.commands import Command
from mouse_virtual.modules.agent_control.desktop import DesktopExecutor
from mouse_virtual.modules.agent_control.executor import AgentExecutor

def test_real_window_search_with_uia():
    root=Path(__file__).resolve().parents[2]
    env=os.environ.copy()
    env.pop("QT_QPA_PLATFORM",None)
    process=subprocess.Popen([sys.executable,str(root/"scripts/uia_lab/fixture.py")],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    try:
        header=process.stdout.readline().strip()
        assert header.startswith("HWND="),header
        hwnd=int(header.split("=",1)[1])
        executor=AgentExecutor(desktop=DesktopExecutor(hwnd))
        assert executor.execute(Command("desktop.fill",auto_id="QApplication.QWidget.search_input",text="perritos"))["verified"]
        assert executor.execute(Command("desktop.invoke",auto_id="QApplication.QWidget.search_button"))["invoked"]
        result=""
        for _ in range(30):
            result=executor.execute(Command("desktop.read_control",auto_id="QApplication.QWidget.search_result",control_type="Text"))["text"]
            if result=="Resultados de perritos":break
            time.sleep(.1)
        assert result=="Resultados de perritos"
    finally:
        process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
