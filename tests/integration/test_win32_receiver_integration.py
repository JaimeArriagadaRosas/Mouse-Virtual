import sys,subprocess,json
from pathlib import Path
def test_isolated_win32_message_receiver():
    script=Path(__file__).resolve().parents[2]/"scripts"/"input_receiver_lab.py"
    result=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,timeout=15,check=True)
    data=json.loads(result.stdout.strip().splitlines()[-1])
    assert data["passed"] is True
    assert data["message_count"]==18
    assert data["all_coordinates_match"] is True
    assert sorted(data["per_button_counts"].values())==[[3,3]]*3
