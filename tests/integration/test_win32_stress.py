from pathlib import Path
import json,subprocess,sys

def test_receiver_1000_clicks_no_global_input():
    root=Path(__file__).resolve().parents[2]
    completed=subprocess.run([sys.executable,str(root/"scripts"/"input_receiver_lab.py"),"--stress-clicks","1000"],capture_output=True,text=True,timeout=15,check=True)
    d=json.loads(completed.stdout)
    assert d["stress_clicks"]==1000
    assert d["message_count"]==2018
    assert d["expected_events"]==2018
    assert d["per_button_counts"]["513"]==[1003,1003]
    assert d["passed"] is True
