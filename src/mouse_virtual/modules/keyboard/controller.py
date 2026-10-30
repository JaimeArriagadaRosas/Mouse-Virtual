"""Mouse Virtual desktop module."""
from PySide6.QtWidgets import QComboBox
from mouse_virtual.app.ui_helpers import label, spin

class KeyboardMixin:
    def keyboard_page(self):
        pane,col=self.pane("Teclado","Pulsaciones globales dirigidas a la ventana con foco")
        self.field(col,"Tecla",self._keyboard_keys())
        self.key_interval=spin(1000,3600000,115);self.key_interval.setSuffix(" ms")
        self.field(col,"Intervalo",self.key_interval)
        self.key_count=spin(10,100000,115);self.field(col,"Repeticiones",self.key_count)
        col.addWidget(label("Aviso: este modo introduce teclas en la aplicación activa.","muted"))
        col.addStretch();return pane

    def _keyboard_keys(self):
        self.key=QComboBox();self.key.addItems(["ESPACIO","ENTER","TAB","ARRIBA","ABAJO","IZQUIERDA","DERECHA"]+[f"F{i}" for i in range(1,13)]+list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        return self.key

