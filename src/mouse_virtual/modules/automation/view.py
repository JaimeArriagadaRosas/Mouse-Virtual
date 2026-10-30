"""Automation workspace layout v0.5.
The controls use the Main window's existing callbacks and persistent sequence store.
Only the presentation is defined here; no dummy sequence data.
"""
from PySide6.QtCore import Qt, QSize
from mouse_virtual.modules.virtual_cursor.preview import PositionPreview
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QComboBox, QLineEdit, QPushButton, QSpinBox,
    QCheckBox, QTableWidget, QHeaderView, QSizePolicy, QAbstractItemView
)

class RepeatSwitch(QCheckBox):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("repeatSwitch")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    def sizeHint(self):
        return QSize(246, 36)
    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cy=self.height()//2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#2563eb") if self.isChecked() else QColor("#b8bdc8"))
        p.drawRoundedRect(1,cy-11,41,22,11,11)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(22 if self.isChecked() else 4,cy-8,16,16)
        p.setPen(QColor("#202d42") if self.isEnabled() else QColor("#9599a3"))
        p.setFont(self.font())
        p.drawText(53,0,max(0,self.width()-53),self.height(),
                   Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,self.text())
        p.end()

def text(value, name=None):
    item=QLabel(value)
    if name:item.setObjectName(name)
    return item

def action(value, callback, role=None):
    button=QPushButton(value)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    if role:button.setObjectName(role)
    button.clicked.connect(callback)
    button.setMinimumHeight(35)
    button.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
    return button

def section(title):
    card=QFrame()
    card.setObjectName("sectionCard")
    col=QVBoxLayout(card)
    col.setContentsMargins(17,13,17,14)
    col.setSpacing(8)
    col.addWidget(text(title,"cardHeading"))
    return card,col

def field(name,control):
    block=QWidget()
    v=QVBoxLayout(block)
    v.setContentsMargins(0,0,0,0);v.setSpacing(5)
    v.addWidget(text(name,"compactFieldLabel"))
    v.addWidget(control)
    return block

def setup_automation_page(host):
    pane=QFrame()
    pane.setObjectName("automationPage")
    outer=QVBoxLayout(pane)
    outer.setContentsMargins(0,0,0,0)
    outer.setSpacing(0)
    scrolling=QScrollArea()
    scrolling.setObjectName("automationScroll")
    scrolling.setWidgetResizable(True)
    scrolling.setFrameShape(QFrame.Shape.NoFrame)
    scrolling.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scrolling.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    canvas=QWidget()
    canvas.setObjectName("automationCanvas")
    col=QVBoxLayout(canvas)
    col.setContentsMargins(0,0,8,3)
    col.setSpacing(7)
    col.addWidget(text("Automatización","automationHeading"))
    col.addWidget(text("Configura destino, grabación y reproducción.","automationSubtitle"))

    # Card 1: target and input mode
    card,container=section("Destino e interacción")
    grid=QGridLayout()
    grid.setHorizontalSpacing(16);grid.setVerticalSpacing(8)
    grid.setColumnMinimumWidth(0,132)
    grid.setColumnStretch(1,1)
    host.target_combo=QComboBox();host.target_combo.setObjectName("automationInput")
    host.target_combo.setMinimumHeight(36)
    host.target_combo.currentIndexChanged.connect(host.update_target_info)
    host.mode_combo=QComboBox();host.mode_combo.setObjectName("automationInput")
    host.mode_combo.addItems(["Simulación (sin clics)","Ventana en segundo plano (Win32)","Entrada global (mouse físico)"])
    host.mode_combo.setCurrentIndex(1)
    host.mode_combo.setMinimumHeight(36)
    grid.addWidget(text("Ventana destino","fieldLabel"),0,0)
    grid.addWidget(host.target_combo,0,1)
    grid.addWidget(text("Modo de entrada","fieldLabel"),1,0)
    grid.addWidget(host.mode_combo,1,1)
    container.addLayout(grid)
    host.target_info=text("","muted")
    host.target_info.hide()
    container.addWidget(host.target_info)
    container.addWidget(text("ⓘ  El modo global puede interferir con otras aplicaciones.","smallInfo"))
    col.addWidget(card)

    # Card 2: the selected saved sequence, rename, and repetition.
    card,container=section("Secuencia guardada")
    row=QHBoxLayout();row.setSpacing(10)
    host.saved_selector=QComboBox()
    host.saved_selector.setObjectName("automationInput")
    host.saved_selector.setMinimumHeight(36)
    host.saved_selector.currentIndexChanged.connect(host.on_automation_selected)
    row.addWidget(field("Secuencia guardada",host.saved_selector),5)
    host.rename_input=QLineEdit()
    host.rename_input.setObjectName("automationInput")
    host.rename_input.setPlaceholderText("Nombre de secuencia")
    host.rename_input.setMinimumHeight(36)
    row.addWidget(field("Nombre",host.rename_input),3)
    rename_btn=action("Renombrar",host.rename_sequence,"smallAction")
    rename_btn.setFixedWidth(105)
    row.addWidget(rename_btn,0,Qt.AlignmentFlag.AlignBottom)
    container.addLayout(row)
    host.record_status=text("No hay secuencias guardadas","smallInfo")
    container.addWidget(host.record_status)
    repeatrow=QHBoxLayout();repeatrow.setSpacing(12)
    host.infinite_check=RepeatSwitch("Repetir indefinidamente")
    host.infinite_check.setChecked(True)
    host.infinite_check.toggled.connect(host.update_repeat_ui)
    repeatrow.addWidget(host.infinite_check,1)
    repeatrow.addStretch(1)
    repeatrow.addWidget(text("Repeticiones","fieldLabel"))
    host.record_repeat=QSpinBox()
    host.record_repeat.setObjectName("automationInput")
    host.record_repeat.setRange(1,10000)
    host.record_repeat.setValue(1)
    host.record_repeat.setEnabled(False)
    host.record_repeat.setFixedWidth(90)
    host.record_repeat.setMinimumHeight(34)
    repeatrow.addWidget(host.record_repeat)
    container.addLayout(repeatrow)
    col.addWidget(card)

    # Card 3: grouped primary/secondary controls.
    card,container=section("Controles de grabación y reproducción")
    first=QHBoxLayout();first.setSpacing(8)
    host.play_record_button=action("▶  Reproducir secuencia",host.start_recorded,"primaryAction")
    first.addWidget(host.play_record_button,3)
    host.automation_stop_button=action("■  Detener",host.stop,"softStop")
    first.addWidget(host.automation_stop_button,2)
    host.automation_record_button=action("●  Grabar  F9",host.toggle_recording,"recordAction")
    first.addWidget(host.automation_record_button,2)
    host.automation_pause_button=action("Ⅱ  Pausar  F10",host.toggle_pause_recording,"secondaryAction")
    first.addWidget(host.automation_pause_button,2)
    container.addLayout(first)
    second=QHBoxLayout();second.setSpacing(8)
    second.addWidget(action("▣  Guardar grabación",host.save_current_recording,"secondaryAction"),3)
    second.addWidget(action("☷  Ver en Secuencias",host.open_selected_sequence,"secondaryAction"),3)
    second.addStretch(2)
    container.addLayout(second)
    col.addWidget(card)

    # Card 4: read-only actual sequence preview (no fabricated rows).
    card,container=section("Vista previa de la secuencia")
    host.record_table=QTableWidget(0,5)
    host.record_table.setObjectName("sequencePreview")
    host.record_table.setHorizontalHeaderLabels(["Paso","Evento","X","Y","Espera ms"])
    host.record_table.verticalHeader().setVisible(False)
    host.record_table.horizontalHeader().setHighlightSections(False)
    host.record_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Fixed)
    host.record_table.horizontalHeader().resizeSection(0,52)
    host.record_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
    for i,w in [(2,85),(3,85),(4,110)]:
        host.record_table.horizontalHeader().setSectionResizeMode(i,QHeaderView.ResizeMode.Fixed)
        host.record_table.horizontalHeader().resizeSection(i,w)
    host.record_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    host.record_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    host.record_table.setAlternatingRowColors(True)
    host.record_table.setMinimumHeight(148)
    host.record_table.setMaximumHeight(175)
    host.record_table.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
    host.record_table.setShowGrid(False)
    container.addWidget(host.record_table)
    host.position_preview=PositionPreview()
    container.addWidget(host.position_preview)
    col.addWidget(card)

    # Do not add redundant controls into the main canvas. The footer owns refresh.
    col.addStretch(0)
    scrolling.setWidget(canvas)
    outer.addWidget(scrolling)
    return pane
