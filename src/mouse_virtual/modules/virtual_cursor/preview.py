"""Embedded position preview. Never draws over the desktop."""
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter,QColor,QPen,QFont
from PySide6.QtCore import Qt,QRectF
from PySide6.QtSvg import QSvgRenderer
from pathlib import Path
class PositionPreview(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setMinimumHeight(108)
        self.setMaximumHeight(155)
        self.position=None
        self.size=(1,1)
        self.status="Sin acciones"
        self.cursor_svg=QSvgRenderer(str(Path(__file__).resolve().parents[2]/"resources"/"cursors"/"black_pointer.svg"))
    def update_step(self,x,y,w,h,status):
        self.position=(int(x),int(y))
        self.size=(max(1,int(w)),max(1,int(h)))
        self.status=status
        self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds=self.rect().adjusted(4,4,-4,-4)
        p.setPen(QPen(QColor("#c9d7e5"),1))
        p.setBrush(QColor("#f4f7fc"))
        p.drawRoundedRect(bounds,8,8)
        if self.position:
            x,y=self.position;w,h=self.size
            px=bounds.left()+round(max(0,min(x,w))*bounds.width()/w)
            py=bounds.top()+round(max(0,min(y,h))*bounds.height()/h)
            if self.cursor_svg.isValid():
                self.cursor_svg.render(p,QRectF(px,py,16,20))
            else:
                p.setPen(QPen(QColor("#111111"),2))
                p.drawEllipse(px-5,py-5,10,10)
        p.setPen(QColor("#56647c"))
        p.setFont(QFont("Segoe UI",9))
        label=self.status
        if self.position:label+=f"  ({self.position[0]}, {self.position[1]})"
        p.drawText(bounds.adjusted(9,8,-4,-4),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop,label)
        p.end()
