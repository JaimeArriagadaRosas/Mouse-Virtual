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


class SettingsMixin:
    def save_settings(self):
        data={"interval":[self.hours.value(),self.minutes.value(),self.seconds.value(),self.millis.value()],
              "button":choice(self.buttons),"clicktype":choice(self.clicktypes),
              "repeat":choice(self.repeats),"count":self.repeat_count.value(),
              "position":choice(self.positions),"x":self.x.value(),"y":self.y.value(),
              "input_mode":self.mode_combo.currentIndex()}
        SETTINGS.parent.mkdir(parents=True,exist_ok=True)
        SETTINGS.write_text(json.dumps(data,indent=2),encoding="utf-8")
        self.summary.setText("Preferencias guardadas")

    def load_settings(self):
        if not SETTINGS.exists():return
        try:
            d=json.loads(SETTINGS.read_text(encoding="utf-8"))
            for w,v in zip((self.hours,self.minutes,self.seconds,self.millis),d.get("interval",[])):w.setValue(v)
            for group,key in [(self.buttons,"button"),(self.clicktypes,"clicktype"),
                              (self.repeats,"repeat"),(self.positions,"position")]:
                ix=d.get(key,0)
                for j,item in enumerate(group):item.setChecked(j==ix)
            self.repeat_count.setValue(d.get("count",100))
            self.x.setValue(d.get("x",100));self.y.setValue(d.get("y",100))
            self.mode_combo.setCurrentIndex(d.get("input_mode",0))
        except Exception:pass

