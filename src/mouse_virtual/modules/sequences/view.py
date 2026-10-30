"""Sequence table and editor view."""
from PySide6.QtWidgets import QComboBox,QLineEdit,QHBoxLayout,QTableWidget,QHeaderView
from mouse_virtual.app.ui_helpers import btn, spin, label

class SequencePageMixin:
    def sequence_page(self):
        pane,col=self.pane("Secuencias","Crea un recorrido de clics y pausas para la ventana elegida")
        self.seq_selector=QComboBox();self.seq_selector.currentIndexChanged.connect(self.on_sequence_selected)
        self.field(col,'Secuencia guardada',self.seq_selector)
        self.seq_name=QLineEdit();self.seq_name.setPlaceholderText('Nombre de secuencia')
        naming=QHBoxLayout();naming.addWidget(self.seq_name);naming.addWidget(btn('Renombrar',self.rename_sequence));naming.addWidget(btn('Duplicar',self.duplicate_sequence));naming.addWidget(btn('Eliminar',self.delete_sequence));col.addLayout(naming)
        col.addWidget(btn('Guardar cambios',self.save_sequence_changes))
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(["Tipo","X","Y","Botón","Pausa ms"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        col.addWidget(self.table)
        actions=QHBoxLayout()
        for txt,func in [("+ Clic",self.add_click),("+ Espera",self.add_wait),("Eliminar",self.remove_step),
                         ("Guardar JSON",self.save_plan),("Cargar JSON",self.load_plan)]:
            actions.addWidget(btn(txt,func,"subtle"))
        col.addLayout(actions)
        self.seq_repeat=spin(1,10000,110);self.field(col,"Repetir secuencia",self.seq_repeat)
        col.addWidget(label("La secuencia utiliza mensajes Win32; cada coordenada es relativa a su ventana.","muted"))
        return pane
