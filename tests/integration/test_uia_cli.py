import os,subprocess,sys,json
from pathlib import Path

def test_desktop_cli_search_local_app():
    root=Path(__file__).resolve().parents[2]
    env=os.environ.copy()
    env["PYTHONPATH"]=str(root/"src")
    env.pop("QT_QPA_PLATFORM",None)
    fixture=subprocess.Popen([sys.executable,str(root/"scripts/uia_lab/fixture.py")],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    try:
        handle=fixture.stdout.readline().strip()
        assert handle.startswith("HWND="),handle
        args=[sys.executable,"-m","mouse_virtual.modules.agent_control.desktop_cli",
              "--hwnd",handle[5:],"--action","search",
              "--auto-id","QApplication.QWidget.search_input","--name","Buscar",
              "--result-id","QApplication.QWidget.search_result","--text","perritos"]
        done=subprocess.run(args,env=env,cwd=root,capture_output=True,text=True,timeout=20)
        assert done.returncode==0,done.stderr
        payload=json.loads(done.stdout)
        assert payload["ok"]
        assert payload["result"]["verified"]
        assert payload["result"]["result"]=="Resultados de perritos"
    finally:
        fixture.terminate()
        try:fixture.wait(timeout=3)
        except subprocess.TimeoutExpired:fixture.kill();fixture.wait(timeout=3)
