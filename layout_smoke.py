import os
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from main import Main
app=QApplication([])
w=Main();w.show_page(4);w.show();app.processEvents()
widgets={"window":w,"stack":w.stack,"automation":w.stack.currentWidget(),"target":w.target_combo,"mode":w.mode_combo,"saved":w.saved_selector,"rename":w.rename_input,"record":w.automation_record_button,"play":w.play_record_button,"table":w.record_table,"run":w.run_button}
for name,obj in widgets.items():
 g=obj.geometry()
 print(name,g.x(),g.y(),g.width(),g.height(),flush=True)
print("STORED_SEQUENCES",w.saved_selector.count(),flush=True)
print("LAYOUT_OK",w.target_combo.height()>=30 and w.record_table.height()>=100,flush=True)
w.grab().save(r"D:\Documentos\MDL\Informatico\Apredizaje\Mouse-Virtual-Lab\Mouse-Virtual\backups\v05_layout_preview.png")
w.close()
