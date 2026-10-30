import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from main import Main
app=QApplication([])
w=Main()
print("SMOKE",len(w.tabs),w.stack.count(),w.target_combo.count(),flush=True)
w.show_page(1);w.show_page(2);w.show_page(0)
w.close()
