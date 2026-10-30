import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from PySide6.QtWidgets import QApplication
from mouse_virtual.app.main_window import Main
app=QApplication([])
w=Main()
print("SMOKE",len(w.tabs),w.stack.count(),w.target_combo.count(),flush=True)
w.show_page(1);w.show_page(2);w.show_page(0)
w.close()
