"""Window fixture for native Windows UIA integration."""
import sys
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QLineEdit,QPushButton,QLabel
app=QApplication([])
window=QWidget()
window.setWindowTitle("MouseVirtual UIA Laboratory")
layout=QVBoxLayout(window)
entry=QLineEdit();entry.setObjectName("search_input");entry.setAccessibleName("Buscar")
button=QPushButton("Buscar");button.setObjectName("search_button");button.setAccessibleName("Buscar")
result=QLabel("Sin resultados");result.setObjectName("search_result")
button.clicked.connect(lambda:result.setText("Resultados de "+entry.text()))
layout.addWidget(entry);layout.addWidget(button);layout.addWidget(result)
window.resize(360,180);window.show()
print("HWND="+str(int(window.winId())),flush=True)
sys.exit(app.exec())
