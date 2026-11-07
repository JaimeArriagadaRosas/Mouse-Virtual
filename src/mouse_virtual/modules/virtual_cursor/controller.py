"""Mouse Virtual desktop module."""
from PySide6.QtWidgets import QHBoxLayout, QWidget
from mouse_virtual.infrastructure.windows.handles import client_size
from mouse_virtual.infrastructure.windows.input import post_click
from mouse_virtual.modules.recording.recorder import window_info, active_window
from mouse_virtual.app.ui_helpers import btn, label, spin

class VirtualCursorMixin:
    def virtual_page(self):
        pane,col=self.pane("Mouse virtual","Cursor independiente para acciones compatibles en segundo plano")
        col.addWidget(label("El cursor negro es visual. Solo las entradas dirigidas a ventana son independientes del mouse real.","muted"))
        line=QWidget();r=QHBoxLayout(line);r.setContentsMargins(0,0,0,0)
        r.addWidget(btn("Mostrar cursor",self.preview));r.addWidget(btn("Ocultar cursor",lambda: (setattr(self.position_preview, 'position', None), self.position_preview.update())));r.addStretch()
        col.addWidget(line)
        line=QWidget();r=QHBoxLayout(line);r.setContentsMargins(0,0,0,0)
        self.vx=spin(100,32767,90);self.vy=spin(100,32767,90)
        r.addWidget(label("X"));r.addWidget(self.vx);r.addWidget(label("Y"));r.addWidget(self.vy)
        r.addWidget(btn("Mover",self.preview));r.addStretch()
        self.field(col,"Posición virtual",line)
        col.addWidget(label("Elige una ventana en Automatización; puedes desplazar el cursor gráfico sin mover el físico.","muted"))
        line=QHBoxLayout()
        for title,dx,dy in [("←",-20,0),("↑",0,-20),("↓",0,20),("→",20,0)]:
            line.addWidget(btn(title,lambda checked=False,a=dx,c=dy:self.move_virtual(a,c)))
        col.addLayout(line)
        col.addWidget(btn("Enviar un clic virtual",self.single_virtual))
        col.addStretch();return pane

    def preview(self):
        hwnd=self.target_combo.currentData()
        if not hwnd:self.report_error("Selecciona primero una ventana.");return
        self.position_preview.update_step(self.vx.value(),self.vy.value(),*client_size(hwnd),'VISUAL_ONLY')

    def move_virtual(self,dx,dy):
        self.vx.setValue(max(0,self.vx.value()+dx));self.vy.setValue(max(0,self.vy.value()+dy))
        self.preview()

    def single_virtual(self):
        hwnd=self.target_combo.currentData()
        if not hwnd:self.report_error("Selecciona una ventana.");return
        try:
            info = window_info(hwnd)
            if str(info.get("class", "")).startswith("Chrome_WidgetWin") and active_window() != hwnd:
                raise PermissionError("Para Chrome en segundo plano, utiliza la sección Pestaña existente.")
            post_click(hwnd,self.vx.value(),self.vy.value())
            self.preview();self.summary.setText('Clic Win32 enviado; recepción no confirmada')
        except Exception as exc:self.report_error(str(exc))

