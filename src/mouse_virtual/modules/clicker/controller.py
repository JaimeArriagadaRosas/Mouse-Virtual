"""Mouse Virtual desktop module."""
from PySide6.QtWidgets import QHBoxLayout, QWidget
from mouse_virtual.app.ui_helpers import divider, label, segment, spin

class ClickerMixin:
    def clicker_page(self):
        pane,col=self.pane("Clicker","Repetición precisa de acciones del mouse")
        times=QWidget();row=QHBoxLayout(times);row.setContentsMargins(0,0,0,0)
        self.hours=spin(0,99,60);self.minutes=spin(0,59,60);self.seconds=spin(0,59,60);self.millis=spin(50,999,70)
        for widget,unit in [(self.hours,"h"),(self.minutes,"m"),(self.seconds,"s"),(self.millis,"ms")]:
            row.addWidget(widget);row.addWidget(label(unit,"muted"))
        row.addStretch()
        self.field(col,"Intervalo",times);col.addWidget(divider())
        line=QWidget();r=QHBoxLayout(line);r.setContentsMargins(0,0,0,0)
        self.buttons=segment(r,["Izquierdo","Derecho","Central"]);r.addStretch()
        self.field(col,"Botón del mouse",line);col.addWidget(divider())
        line=QWidget();r=QHBoxLayout(line);r.setContentsMargins(0,0,0,0)
        self.clicktypes=segment(r,["Simple","Doble"]);r.addStretch()
        self.field(col,"Tipo de clic",line);col.addWidget(divider())
        line=QWidget();r=QHBoxLayout(line);r.setContentsMargins(0,0,0,0)
        self.repeats=segment(r,["Hasta detener","Cantidad fija"],1)
        self.repeat_count=spin(100,100000,96);r.addWidget(self.repeat_count);r.addStretch()
        self.field(col,"Repetir",line);col.addWidget(divider())
        line=QWidget();r=QHBoxLayout(line);r.setContentsMargins(0,0,0,0)
        self.positions=segment(r,["Seguir cursor","Punto fijo","Ventana"],2);r.addStretch()
        self.field(col,"Posición",line)
        col.addWidget(label("La opción Ventana no desplaza el cursor físico.","muted"))
        line=QWidget();r=QHBoxLayout(line);r.setContentsMargins(0,0,0,0)
        self.x=spin(100,32767,88);self.y=spin(100,32767,88)
        r.addWidget(label("X"));r.addWidget(self.x);r.addWidget(label("Y"));r.addWidget(self.y);r.addStretch()
        self.field(col,"Coordenadas",line)
        col.addStretch()
        return pane

    def interval_ms(self):
        return ((self.hours.value()*3600+self.minutes.value()*60+self.seconds.value())*1000+self.millis.value())

