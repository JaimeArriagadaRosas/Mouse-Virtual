"""Compatibility launcher for Windows and PyInstaller."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/"src"))
from mouse_virtual.app.main_window import Main
from mouse_virtual.app.bootstrap import main

if __name__=="__main__":
    main()
