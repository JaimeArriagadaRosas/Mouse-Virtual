import json,os,subprocess,sys
from pathlib import Path

def test_remote_cli_real_window_plan(tmp_path):
    root=Path(__file__).resolve().parents[2]
    env=os.environ.copy()
    env["PYTHONPATH"]=str(root/"src")
    env.pop("QT_QPA_PLATFORM",None)
    proc=subprocess.Popen([sys.executable,str(root/"scripts/uia_lab/fixture.py")],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    try:
        line=proc.stdout.readline().strip()
        assert line.startswith("HWND="),line
        hwnd=line[5:]
        plan={"steps":[
            {"action":"desktop.fill","auto_id":"QApplication.QWidget.search_input","text":"perritos"},
            {"action":"desktop.invoke","auto_id":"QApplication.QWidget.search_button","control_type":"Button"},
            {"action":"desktop.wait_text","auto_id":"QApplication.QWidget.search_result","control_type":"Text","text":"Resultados de perritos"}]}
        f=tmp_path/"plan.json"
        f.write_text(json.dumps(plan),encoding="utf8")
        cmd=[sys.executable,"-m","mouse_virtual.modules.agent_control.remote_cli","run","--hwnd",hwnd,"--authorize-hwnd",hwnd,"--plan",str(f)]
        result=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True,timeout=20)
        assert result.returncode==0,result.stderr
        payload=json.loads(result.stdout)
        assert payload["completed"]==3
        assert payload["results"][0]["result"]["verified"]
        assert payload["results"][1]["result"]["invoked"]
        assert payload["results"][2]["action"]=="desktop.wait_text"
        assert payload["results"][2]["result"]["verified"]
    finally:
        proc.terminate()
        try:proc.wait(timeout=3)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=3)
