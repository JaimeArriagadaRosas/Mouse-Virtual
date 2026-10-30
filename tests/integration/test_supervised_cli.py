import json,os,subprocess,sys
from pathlib import Path

def execute(*args):
    root=Path(__file__).resolve().parents[2]
    env=os.environ.copy()
    env["PYTHONPATH"]=str(root/"src")
    return subprocess.run([sys.executable,"-m","mouse_virtual.modules.agent_control.supervised_cli",*args],capture_output=True,text=True,timeout=15,env=env)

def test_supervised_windows():
    p=execute("--timeout","10","windows")
    assert p.returncode==0,p.stderr
    assert json.loads(p.stdout)["ok"]

def test_supervisor_rejects_unscoped_actions():
    p=execute("--timeout","5","run")
    assert p.returncode!=0
    assert json.loads(p.stdout)["ok"] is False
