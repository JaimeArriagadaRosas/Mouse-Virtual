"""Qt UI primitives shared across pages."""
from pathlib import Path
from PySide6.QtWidgets import QLabel,QPushButton,QFrame,QSpinBox

HERE=Path(__file__).resolve().parents[1]/"resources"

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
