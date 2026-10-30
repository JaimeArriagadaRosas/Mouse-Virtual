"""Mouse Virtual: custom PySide6 desktop shell with distinct input modes."""
import sys,time,json,ctypes
from ctypes import wintypes
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QPoint
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QKeySequence,QShortcut,QAction,QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QFrame,QLabel,QPushButton,
 QVBoxLayout,QHBoxLayout,QGridLayout,QSpinBox,QComboBox,QCheckBox,QStackedWidget,
 QTableWidget,QTableWidgetItem,QHeaderView,QMessageBox,QFileDialog,QLineEdit,QSystemTrayIcon,QMenu)
from mouse_virtual.infrastructure.windows.handles import windows, client_size, client_to_screen, cursor_pos
from mouse_virtual.infrastructure.windows.input import post_click, native_click, native_key
from mouse_virtual.modules.sequences.models import Plan,Step
from mouse_virtual.modules.sequences.repository import SequenceStore
from mouse_virtual.modules.automation.view import setup_automation_page
from mouse_virtual.modules.playback.engine import SessionLog,Playback
from mouse_virtual.modules.recording.recorder import MouseRecorder,window_info,active_window
from mouse_virtual.infrastructure.geometry import snapshot,compare,legacy_geometry,transform

HERE=Path(__file__).resolve().parents[1]/"resources"
SETTINGS=Path.home()/"AppData"/"Local"/"MouseVirtual"/"settings.json"

def label(text,name=None):
    w=QLabel(text)
    if name:w.setObjectName(name)
    return w
def btn(text,fn=None,name=None):
    w=QPushButton(text)
    if name:w.setObjectName(name)
    if fn:w.clicked.connect(fn)
    return w
def segment(layout,labels,default=0):
    group=[]
    for i,text in enumerate(labels):
        w=btn(text,name="segment");w.setCheckable(True);w.setChecked(i==default)
        layout.addWidget(w);group.append(w)
    for w in group:w.clicked.connect(lambda _,a=w: [x.setChecked(x is a) for x in group])
    return group
def choice(group):
    return next((i for i,w in enumerate(group) if w.isChecked()),0)
def divider():
    w=QFrame();w.setObjectName("separator");w.setFixedHeight(1);return w
def spin(value=0,maxv=999999,width=76):
    w=QSpinBox();w.setRange(0,maxv);w.setValue(value);w.setFixedWidth(width);return w


class LayoutMixin:
    def build(self):
        root=QWidget();root.setObjectName("root");self.setCentralWidget(root)
        outer=QVBoxLayout(root);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        header=QFrame();header.setObjectName("topbar")
        hl=QHBoxLayout(header);hl.setContentsMargins(24,14,24,14)
        hl.addWidget(label("◈  Mouse Virtual","logo"));hl.addSpacing(18)
        self.tabs=[]
        for i,title in enumerate(["Clicker","Teclado","Secuencias","Mouse virtual","Automatización"]):
            w=btn(title,lambda checked=False,index=i:self.show_page(index),"tab");w.setCheckable(True)
            self.tabs.append(w);hl.addWidget(w)
        hl.addStretch()
        self.compact=btn("▣  Compacto",self.toggle_compact);hl.addWidget(self.compact)
        outer.addWidget(header)
        body=QHBoxLayout();body.setContentsMargins(28,22,24,18);body.setSpacing(24)
        self.stack=QStackedWidget()
        for view in [self.clicker_page(),self.keyboard_page(),self.sequence_page(),self.virtual_page(),self.automation_page()]:
            self.stack.addWidget(view)
        body.addWidget(self.stack,stretch=1)
        body.addWidget(self.run_panel(),stretch=0,alignment=Qt.AlignmentFlag.AlignTop)
        outer.addLayout(body,stretch=1)
        footer=QFrame();footer.setObjectName("topbar")
        fl=QHBoxLayout(footer);fl.setContentsMargins(25,11,25,11)
        fl.addWidget(btn("Guardar como predeterminado",self.save_settings,"subtle"))
        fl.addStretch()
        fl.addWidget(label("Ctrl+Shift+F12: parada de emergencia","muted"))
        fl.addWidget(btn("Actualizar ventanas",self.populate_windows,"subtle"))
        outer.addWidget(footer)

    def field(self,layout,name,widget):
        row=QHBoxLayout();row.setSpacing(14)
        heading=label(name,"fieldLabel");heading.setFixedWidth(138)
        row.addWidget(heading);row.addWidget(widget,stretch=1);layout.addLayout(row)

    def pane(self,title,subtitle):
        pane=QFrame();pane.setObjectName("contentPane")
        col=QVBoxLayout(pane);col.setContentsMargins(0,0,0,0);col.setSpacing(18)
        col.addWidget(label(title,"sectionTitle"));col.addWidget(label(subtitle,"sectionInfo"))
        col.addSpacing(4)
        return pane,col

    def run_panel(self):
        panel=QFrame();panel.setObjectName("runPanel")
        panel.setMinimumWidth(370)
        panel.setMaximumWidth(425)
        panel.setMinimumHeight(495)
        panel.setMaximumHeight(735)
        col=QVBoxLayout(panel);col.setContentsMargins(22,22,22,22);col.setSpacing(14)
        self.state=label("●  Preparado","runState")
        col.addWidget(self.state)
        self.counter=label("0","counter");col.addWidget(self.counter)
        col.addWidget(label("acciones emitidas","runMuted"))
        col.addWidget(divider())
        row=QHBoxLayout();left=QVBoxLayout();right=QVBoxLayout()
        left.addWidget(label("Transcurrido","runMuted"))
        self.elapsed=label("00:00.0","rate");left.addWidget(self.elapsed)
        right.addWidget(label("Velocidad media","runMuted"))
        self.rate=label("0 / s","rate");right.addWidget(self.rate)
        row.addLayout(left);row.addLayout(right);col.addLayout(row)
        self.summary=label("Listo para ejecutar","runMuted");self.summary.setWordWrap(True)
        col.addWidget(self.summary)
        col.addWidget(label('Posición virtual · vista interna','runMuted'))
        col.addWidget(self.position_preview)
        col.addStretch()
        self.run_button=btn("▶  Iniciar   F6",self.toggle,"start");col.addWidget(self.run_button)
        self.stop_button=btn("■  Detener   F7",self.stop,"stop");col.addWidget(self.stop_button)
        col.addWidget(label("F6 iniciar · F7 detener · F8 alternar","runMuted"))
        return panel

    def show_page(self,index):
        self.stack.setCurrentIndex(index)
        for i,tab in enumerate(self.tabs):tab.setChecked(i==index)
        self.mode=["clicker","keyboard","sequence","virtual","automation"][index]
        if index==4 and self.selected_sequence_id:
            try:
                data=self.store.get(self.selected_sequence_id)
                self.summary.setText(f"Secuencia: {data['name']} · {'Bucle infinito' if self.infinite_check.isChecked() else f'{self.record_repeat.value()} repeticiones'}")
            except Exception:self.summary.setText("Secuencia no disponible")
        else:self.summary.setText(f"Sección: {self.tabs[index].text()}")

    def restore_window(self):
        self.showNormal();self.raise_();self.activateWindow()

    def update_repeat_ui(self,checked):
        self.record_repeat.setEnabled(not checked)
        self.seq_repeat.setValue(1 if checked else self.record_repeat.value())

    def toggle_compact(self):
        compact=self.stack.isVisible()
        self.stack.setVisible(not compact)
        self.resize(410 if compact else 1050,550 if compact else 650)
        self.setMinimumWidth(390 if compact else 920)
        self.compact.setText("Expandir" if compact else "▣  Compacto")

    def report_error(self,msg):
        QMessageBox.warning(self,"Mouse Virtual",str(msg))

