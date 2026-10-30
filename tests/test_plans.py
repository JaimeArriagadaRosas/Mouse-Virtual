import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plans import Plan,Step

def test_roundtrip():
    root=Path(__file__).resolve().parents[1]
    with TemporaryDirectory(dir=root) as temporary:
        filename=Path(temporary)/"plan.json"
        plan=Plan([Step("click",10,20),Step("wait",delay_ms=100)],3)
        plan.save(filename)
        assert Plan.load(filename)==plan

def test_validation():
    with pytest.raises(ValueError):Plan([Step("exec",10,20)]).validate()
    with pytest.raises(ValueError):Plan([Step("click",-1,20)]).validate()
    with pytest.raises(ValueError):Plan([Step("click",10,20)],-1).validate()
