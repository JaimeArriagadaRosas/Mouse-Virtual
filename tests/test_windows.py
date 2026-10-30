import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import windows, client_size

def test_window_enumeration():
    results = windows()
    assert isinstance(results, list)
    assert all(isinstance(hwnd, int) and isinstance(title, str) for hwnd, title in results)

def test_bad_window_size():
    assert client_size(0) == (0, 0)
