"""Mouse Virtual: custom PySide6 desktop shell with distinct input modes."""
import sys,time,json,ctypes
from ctypes import wintypes
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QPoint
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QKeySequence,QShortcut,QAction,QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QFrame,QLabel,QPushButton,
 QVBoxLayout,QHBoxLayout,QGridLayout,QSpinBox,QComboBox,QCheckBox,QStackedWidget,
 QTableWidget,QTableWidgetItem,QHeaderView,QMessageBox,QFileDialog,QLineEdit,QSystemTrayIcon,QMenu)
from win32_core import windows,client_size,client_to_screen,cursor_pos,post_click,native_click,native_key
from plans import Plan,Step
from sequence_store import SequenceStore
from automation_view import setup_automation_page
from runtime_v03 import SessionLog,Playback
from recorder import MouseRecorder,window_info,active_window
from geometry import snapshot,compare,legacy_geometry,transform

HERE=Path(__file__).resolve().parent
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

class Overlay(QWidget):
    def __init__(self):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput,True)
        self.setGeometry(QApplication.primaryScreen().virtualGeometry())
        self.position=QPoint(-100,-100)
    def place(self,hwnd,x,y):
        try:
            sx,sy=client_to_screen(hwnd,x,y)
            self.position=QPoint(sx-self.geometry().x(),sy-self.geometry().y())
            self.update()
        except Exception:pass
    def paintEvent(self,_):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("#00bd88"),2));p.setBrush(QColor(0,189,136,45))
        x,y=self.position.x(),self.position.y()
        p.drawEllipse(QPoint(x,y),14,14);p.drawLine(x-22,y,x+22,y);p.drawLine(x,y-22,x,y+22)
        p.setFont(QFont("Segoe UI",9,QFont.Weight.Bold));p.drawText(x+18,y-10,"VIRTUAL")

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Virtual")
        self.resize(1450,875);self.setMinimumSize(1010,675)
        self.setObjectName("window")
        self.overlay=Overlay();self.running=False;self.sent=0;self.start_time=0;self.target=None
        self.recorder=MouseRecorder();self.recorded=[];self.record_paused=False;self.recording_geometry=None
        self.session_log=SessionLog()
        self.playback=Playback(self.session_log,lambda *args:self.playback_events.append(('progress',args)),lambda *args:self.playback_events.append(('ended',args)))
        self.playback_events=[]
        self.visual_events=[]
        self.automation_default=False
        self.store=SequenceStore();self.selected_sequence_id=None;self._syncing=False;self.last_recording_saved=True
        self.recorder_timer=QTimer(self);self.recorder_timer.timeout.connect(self.poll_recording);self.recorder_timer.start(80)
        self.playback_timer=QTimer(self);self.playback_timer.timeout.connect(self.poll_playback);self.playback_timer.start(100)
        self.mode="clicker";self.steps=[];self.sequence_cursor=0;self.sequence_repeated=0
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick)
        self.monitor=QTimer(self);self.monitor.timeout.connect(self.refresh_stats);self.monitor.start(120)
        self.hotkey=QTimer(self);self.hotkey.timeout.connect(self.emergency);self.hotkey.start(65)
        self.was_stop=False;self.was_record=False;self.was_pause=False
        self.build()
        self.populate_windows()
        self.load_settings()
        self.refresh_sequences()
        for key,action in [("F6",self.start),("F7",self.stop),("F8",self.toggle)]:
            shortcut=QShortcut(QKeySequence(key),self);shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut);shortcut.activated.connect(action)
        self.show_page(0)
        self.tray=QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        menu=QMenu(self)
        menu.addAction('Mostrar Mouse Virtual',self.restore_window)
        menu.addAction('Detener reproducción',self.stop)
        menu.addAction('Detener grabación',self.finish_recording)
        menu.addAction('Salir',self.close)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason:self.restore_window() if reason==QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.tray.show()
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
    def virtual_page(self):
        pane,col=self.pane("Mouse virtual","Cursor independiente para acciones compatibles en segundo plano")
        col.addWidget(label("El cursor verde es visual. Solo las entradas dirigidas a ventana son independientes del mouse real.","muted"))
        line=QWidget();r=QHBoxLayout(line);r.setContentsMargins(0,0,0,0)
        r.addWidget(btn("Mostrar cursor",self.preview));r.addWidget(btn("Ocultar cursor",self.overlay.hide));r.addStretch()
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
    def automation_page(self):
        return setup_automation_page(self)
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
    def populate_windows(self):
        previous=self.target_combo.currentData() if hasattr(self,"target_combo") else None
        self.target_combo.clear()
        for hwnd,title in windows():
            if "Mouse Virtual" not in title:self.target_combo.addItem(title,hwnd)
        pos=self.target_combo.findData(previous)
        if pos>=0:self.target_combo.setCurrentIndex(pos)
        self.update_target_info()
    def bind_foreground(self):
        hwnd=active_window()
        if not hwnd:return
        current=self.target_combo.findData(hwnd)
        if current<0:
            self.populate_windows()
            current=self.target_combo.findData(hwnd)
        if current>=0:self.target_combo.setCurrentIndex(current)
        else:self.report_error('La ventana activa no está disponible para selección.')
    def update_target_info(self):
        hwnd=self.target_combo.currentData()
        if hwnd:
            w,h=client_size(hwnd)
            info=window_info(hwnd)
            self.target_info.setText(f"PID: {info['pid']} · Cliente: {w} × {h} · Minimizada: {info['minimized']}")
            self.target_combo.setToolTip(self.target_info.text()+f" · Clase: {info['class']} · Exterior: {info['outer']}")
    def restore_window(self):
        self.showNormal();self.raise_();self.activateWindow()
    def finish_recording(self):
        if self.recorder.is_running:self.toggle_recording()
    def toggle_recording(self):
        if self.recorder.is_running:
            self.recorder.stop();self.poll_recording()
            self.session_log.write('RECORD_END',count=len(self.recorded),diagnostics=self.recorder.diagnostics())
            self.showNormal();self.raise_();self.activateWindow()
            self.record_status.setText(f'Grabación finalizada: {len(self.recorded)} acciones') if self.recorded else self.record_status.setText('Sin clics del destino: revisa ventana y foco')
            self.automation_record_button.setText('●  Grabar  F9')
            if self.recorded:self.save_recording_as_sequence()
            return
        hwnd=self.target_combo.currentData()
        if not hwnd:
            self.report_error('Selecciona primero una ventana destino.');return
        try:
            self.recorded=[];self.record_table.setRowCount(0);self.record_paused=False
            self.session_log.write('RECORD_UI_START',hwnd=hwnd)
            self.last_recording_saved=False
            self.recorder.start(hwnd)
            self.recording_geometry=snapshot(hwnd)
            self.session_log.write('RECORD_GEOMETRY',geometry=self.recording_geometry)
            self.session_log.write('RECORD_START',hwnd=hwnd,window=window_info(hwnd))
            self.hide()
            self.automation_record_button.setText('■  Terminar  F9')
            self.record_status.setText('Grabando… presiona F9 para terminar')
        except Exception as exc:self.report_error(str(exc))
    def toggle_pause_recording(self):
        if not self.recorder.is_running:return
        self.record_paused=not self.record_paused
        self.recorder.set_paused(self.record_paused)
        self.session_log.write('RECORD_PAUSE_TOGGLE',paused=self.record_paused)
        self.record_status.setText('En pausa (los clics se descartan)' if self.record_paused else '● Grabando')
    def poll_recording(self):
        for event in self.recorder.poll():
            if self.record_paused:continue
            if event['type']!='click':continue
            self.recorded.append(event)
            self.session_log.write('INPUT_RECORDED',**event)
            row=self.record_table.rowCount();self.record_table.insertRow(row)
            name={'left':'Clic izquierdo','right':'Clic derecho','middle':'Clic central'}.get(event['button'],event['button'])
            for i,item in enumerate([row+1,name,event['x'],event['y'],event['delay_ms']]):
                self.record_table.setItem(row,i,QTableWidgetItem(str(item)))
    def update_repeat_ui(self,checked):
        self.record_repeat.setEnabled(not checked)
        self.seq_repeat.setValue(1 if checked else self.record_repeat.value())
    def refresh_sequences(self,chosen=None):
        selected=chosen or self.selected_sequence_id
        self._syncing=True
        for combo in (self.saved_selector,self.seq_selector):
            combo.clear()
            for item in self.store.list():
                combo.addItem(item['name'],item['id'])
            index=combo.findData(selected)
            if index>=0:combo.setCurrentIndex(index)
        self._syncing=False
        current=self.saved_selector.currentData()
        if current:self.load_selected(current)
        else:
            self.selected_sequence_id=None
            self.table.setRowCount(0)
            self.record_table.setRowCount(0)
            self.play_record_button.setText('▶  Reproducir secuencia')
            self.record_status.setText('No hay secuencias guardadas')
            self.rename_input.clear()
            self.summary.setText('No hay secuencia seleccionada')
    def on_sequence_selected(self,index):
        if not self._syncing:self.load_selected(self.seq_selector.currentData())
    def on_automation_selected(self,index):
        if not self._syncing:self.load_selected(self.saved_selector.currentData())
    def load_selected(self,seq_id):
        if not seq_id:return
        try:data=self.store.get(seq_id)
        except Exception as exc:self.session_log.write('SEQUENCE_LOAD_ERROR',error=str(exc));return
        self.selected_sequence_id=seq_id
        self._syncing=True
        for combo in (self.saved_selector,self.seq_selector):
            i=combo.findData(seq_id)
            if i>=0:combo.setCurrentIndex(i)
        self.rename_input.setText(data['name'])
        self.seq_name.setText(data['name'])
        self.table.setRowCount(0)
        self.record_table.setRowCount(0)
        for step in data['steps']:
            self.add_table_row(step['action'],step['x'],step['y'],step['button'],step['delay_ms'])
            row=self.record_table.rowCount();self.record_table.insertRow(row)
            button={'left':'Clic izquierdo','right':'Clic derecho','middle':'Clic central'}.get(step['button'],step['button'])
            action=button if step['action']=='click' else 'Esperar'
            for j,value in enumerate((row+1,action,step['x'] if step['action']=='click' else '—',step['y'] if step['action']=='click' else '—',step['delay_ms'])):
                self.record_table.setItem(row,j,QTableWidgetItem(str(value)))
        self.recorded=[dict(type=s['action'],button=s['button'],x=s['x'],y=s['y'],delay_ms=s['delay_ms']) for s in data['steps']]
        self.infinite_check.setChecked(data['infinite'])
        self.record_repeat.setValue(data.get('repeat',1))
        self.seq_repeat.setValue(0 if data['infinite'] else data.get('repeat',1))
        self.play_record_button.setText('▶  Reproducir secuencia')
        self.record_status.setText(f"Última grabación: {len(data['steps'])} acciones")
        self.summary.setText(f"Secuencia: {data['name']} · {'Bucle infinito' if data['infinite'] else str(data.get('repeat',1))+' repeticiones'}")
        self.last_recording_saved=True
        self._syncing=False
    def rename_sequence(self):
        if not self.selected_sequence_id:return
        name=(self.rename_input.text() if self.mode=='automation' else self.seq_name.text()).strip()
        try:
            self.store.update(self.selected_sequence_id,name=name)
            self.refresh_sequences(self.selected_sequence_id)
        except Exception as exc:self.report_error(str(exc))
    def save_sequence_changes(self):
        if not self.selected_sequence_id:return
        try:
            steps=self.current_plan().steps
            self.store.update(self.selected_sequence_id,steps=steps,infinite=self.infinite_check.isChecked(),repeat=self.record_repeat.value())
            self.refresh_sequences(self.selected_sequence_id)
        except Exception as exc:self.report_error(str(exc))
    def duplicate_sequence(self):
        if not self.selected_sequence_id:return
        try:
            data=self.store.duplicate(self.selected_sequence_id)
            self.refresh_sequences(data['id'])
        except Exception as exc:self.report_error(str(exc))
    def delete_sequence(self):
        if not self.selected_sequence_id:return
        if QMessageBox.question(self,'Eliminar secuencia','¿Eliminar la secuencia seleccionada?')!=QMessageBox.StandardButton.Yes:return
        self.store.delete(self.selected_sequence_id)
        self.selected_sequence_id=None
        self.refresh_sequences()
    def save_recording_as_sequence(self):
        if not self.recorded:return
        try:
            steps=[Step('click',max(0,x['x']),max(0,x['y']),x['button'],x['delay_ms']) for x in self.recorded]
            data=self.store.create(steps,infinite=True,target_title=self.target_combo.currentText(),geometry=self.recording_geometry)
            self.session_log.write('SEQUENCE_SAVED',id=data['id'],name=data['name'],steps=len(steps))
            self.last_recording_saved=True
            self.refresh_sequences(data['id'])
        except Exception as exc:
            self.session_log.write('SEQUENCE_SAVE_ERROR',error=str(exc))
            self.report_error(f'No se pudo guardar la grabación: {exc}')
    def save_current_recording(self):
        if self.recorder.is_running:
            self.report_error('Termina la grabación antes de guardarla.');return
        if not self.recorded:
            self.report_error('No hay grabación para guardar.');return
        if self.last_recording_saved and self.selected_sequence_id:
            self.record_status.setText('La grabación ya está guardada')
            return
        self.save_recording_as_sequence()
    def open_selected_sequence(self):
        if not self.selected_sequence_id:
            self.report_error('Selecciona una secuencia antes de abrirla.');return
        self.show_page(2)
    def sync_recorded_to_sequence(self):
        self.table.setRowCount(0)
        for event in self.recorded:
            self.add_table_row('click',max(0,event['x']),max(0,event['y']),event['button'],event['delay_ms'])
        self.seq_repeat.setValue(self.record_repeat.value())
        self.play_record_button.setText(f'▶ Reproducir grabación ({len(self.recorded)} acciones)')
    def start_recorded(self):
        if self.recorder.is_running:
            self.report_error('Finaliza primero la grabación con F9.');return
        if not self.selected_sequence_id:
            self.report_error('Selecciona o graba una secuencia primero.');return
        self.start_sequence_direct()
    def start_sequence_direct(self):
        if self.running:return
        self.action_mode='sequence'
        self.input_mode=self.mode_combo.currentIndex()
        self.target=self.target_combo.currentData()
        if self.input_mode not in (0,1,2):raise ValueError('Modo inválido')
        if not self.target:
            self.report_error('Selecciona una ventana destino.');return
        try:
            data=self.store.get(self.selected_sequence_id)
            self.active_plan=Plan([Step(**x) for x in data['steps']],0 if self.infinite_check.isChecked() else self.record_repeat.value())
            self.active_plan.validate()
            self.sent=0;self.start_time=time.monotonic();self.finished_elapsed=None
            mode={0:'simulation',1:'win32',2:'global'}[self.mode_combo.currentIndex()]
            if mode=='global':
                if window_info(self.target)['pid']!=window_info(active_window())['pid']:
                    self.report_error('El modo global requiere Roblox u otra ventana destino en primer plano.');return
                answer=QMessageBox.warning(self,'Entrada física global','Este modo mueve tu mouse real y puede interferir con tu trabajo. ¿Iniciar?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
                if answer!=QMessageBox.StandardButton.Yes:return
            record_geom=data.get('geometry')
            current=snapshot(self.target)
            if record_geom:
                condition=compare(record_geom,current)
                self.session_log.write('GEOMETRY_CHECK',status=condition,recorded=record_geom,current=current)
                if condition=='invalid':raise ValueError('Geometría inválida')
            else:
                self.session_log.write('GEOMETRY_CHECK',status='legacy',current=current)
            self.playback.start(self.active_plan,self.target,mode=mode,recording_geometry=record_geom)
            self.running=True
            self.state.setText('●  Ejecutando');self.run_button.setText('■  Detener   F7')
            self.summary.setText('Reproduciendo secuencia grabada')
            self.session_log.write('GUI_START',mode='sequence',target=self.target,source='automation')
        except Exception as exc:self.report_error(str(exc))
    def transfer_recording(self):
        self.recorder.stop();self.poll_recording()
        if not self.recorded:
            self.report_error('No hay clics grabados para transferir.');return
        if not self.selected_sequence_id:self.save_recording_as_sequence()
        self.show_page(2)
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
            post_click(hwnd,self.vx.value(),self.vy.value())
            self.preview();self.summary.setText('Clic Win32 enviado; recepción no confirmada')
        except Exception as exc:self.report_error(str(exc))
    def add_click(self):
        self.add_table_row("click",self.x.value(),self.y.value(),"left",50)
    def add_wait(self):
        self.add_table_row("wait",0,0,"left",500)
    def add_table_row(self,action,x,y,button,delay):
        i=self.table.rowCount();self.table.insertRow(i)
        for j,v in enumerate((action,x,y,button,delay)):
            self.table.setItem(i,j,QTableWidgetItem(str(v)))
    def remove_step(self):
        i=self.table.currentRow()
        if i>=0:self.table.removeRow(i)
    def current_plan(self):
        steps=[]
        for i in range(self.table.rowCount()):
            parts=[self.table.item(i,j).text() if self.table.item(i,j) else "" for j in range(5)]
            steps.append(Step(parts[0],int(parts[1]),int(parts[2]),parts[3],int(parts[4])))
        repeat=0 if hasattr(self,'infinite_check') and self.infinite_check.isChecked() else self.record_repeat.value()
        p=Plan(steps,repeat);p.validate()
        return p
    def save_plan(self):
        try:
            plan=self.current_plan()
            path,_=QFileDialog.getSaveFileName(self,"Guardar secuencia","","JSON (*.json)")
            if path:plan.save(path)
        except Exception as exc:self.report_error(str(exc))
    def load_plan(self):
        path,_=QFileDialog.getOpenFileName(self,"Abrir secuencia","","JSON (*.json)")
        if not path:return
        try:
            plan=Plan.load(path);self.table.setRowCount(0)
            for step in plan.steps:self.add_table_row(step.action,step.x,step.y,step.button,step.delay_ms)
            self.seq_repeat.setValue(plan.repeat)
        except Exception as exc:self.report_error(str(exc))
    def interval_ms(self):
        return ((self.hours.value()*3600+self.minutes.value()*60+self.seconds.value())*1000+self.millis.value())
    def start(self):
        if self.running:return
        self.action_mode=self.mode
        if self.action_mode=='automation':
            self.start_recorded();return
        if self.action_mode=='virtual':
            self.report_error('Selecciona Clicker, Teclado o Secuencias.');return
        self.input_mode=self.mode_combo.currentIndex()
        self.target=self.target_combo.currentData()
        if self.action_mode=="sequence":
            try:self.active_plan=self.current_plan()
            except Exception as exc:self.report_error(str(exc));return
        if self.action_mode in ("clicker","sequence") and self.input_mode==0:
            if not self.target:self.report_error("Selecciona una ventana destino en Automatización.");return
            if self.action_mode=="clicker":
                if choice(self.positions)==0:
                    self.report_error("Seguir cursor requiere Entrada global. Elige Punto fijo o Ventana.");return
                if choice(self.positions)==1:
                    self.report_error("Punto fijo de pantalla requiere Entrada global; usa Ventana.");return
        if self.action_mode=="sequence" and self.input_mode==2:
            self.report_error("Secuencias globales aún no están disponibles; selecciona modo Win32.");return
        if self.action_mode=="keyboard" and self.input_mode!=2:
            self.report_error("El teclado actual utiliza entrada global; selecciona Entrada global.");return
        delay=(self.interval_ms() if self.action_mode=="clicker" else
               self.key_interval.value() if self.action_mode=="keyboard" else 50)
        if delay<50:self.report_error("Intervalo mínimo: 50 ms.");return
        if self.action_mode=="clicker" and self.input_mode==2:
            answer=QMessageBox.warning(self,"Modo global","El modo global puede mover el puntero físico e interferir con otras aplicaciones. ¿Continuar?",
                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if answer!=QMessageBox.StandardButton.Yes:return
        self.sent=0;self.start_time=time.monotonic();self.running=True
        self.finished_elapsed=None
        self.sequence_cursor=0;self.sequence_repeated=0
        self.state.setText("●  Ejecutando");self.run_button.setText("■  Detener   F7")
        if self.action_mode=='sequence':
            try:self.playback.start(self.active_plan,self.target,mode='simulation' if self.input_mode==0 else 'win32',recording_geometry=None)
            except Exception as exc:self.stop();self.report_error(str(exc));return
        else:self.timer.start(delay)
        self.session_log.write('GUI_START',mode=self.action_mode,target=self.target)
        self.summary.setText("Acciones enviadas, no equivalen a recepción confirmada.")
    def toggle(self):
        if self.running:self.stop()
        else:self.start()
    def tick(self):
        try:
            if self.action_mode=="clicker":
                button=["left","right","middle"][choice(self.buttons)]
                count=2 if choice(self.clicktypes)==1 else 1
                if self.input_mode==1:
                    post_click(self.target,self.x.value(),self.y.value(),button,count)
                    self.position_preview.update_step(self.x.value(),self.y.value(),*client_size(self.target),'POSTED_UNCONFIRMED')
                elif self.input_mode==2:
                    point=None if choice(self.positions)==0 else (
                        (self.x.value(),self.y.value()) if choice(self.positions)==1 else
                        client_to_screen(self.target,self.x.value(),self.y.value()))
                    native_click(button,count,point)
                self.sent+=count
                if choice(self.repeats)==1 and self.sent>=self.repeat_count.value():self.stop()
            elif self.action_mode=="keyboard":
                native_key(self.key.currentText());self.sent+=1
                if self.sent>=self.key_count.value():self.stop()
            elif self.action_mode=="sequence":
                step=self.active_plan.steps[self.sequence_cursor]
                if step.action=="click":
                    post_click(self.target,step.x,step.y,step.button);self.sent+=1
                    self.position_preview.update_step(step.x,step.y,*client_size(self.target),'POSTED_UNCONFIRMED')
                self.sequence_cursor+=1
                if self.sequence_cursor>=len(self.active_plan.steps):
                    self.sequence_cursor=0;self.sequence_repeated+=1
                    if self.sequence_repeated>=self.active_plan.repeat:self.stop();return
                self.timer.start(max(50,step.delay_ms))
        except Exception as exc:
            self.stop();self.report_error(f"Ejecución detenida: {exc}")
    def poll_playback(self):
        while self.playback_events:
            kind,args=self.playback_events.pop(0)
            if kind=='progress':
                count,total,repeat,index,*extra=args
                self.sent=count
                self.summary.setText(f'Progreso: {count}/{total if total is not None else "∞"} · vuelta {repeat+1} · paso {index+1}')
                if len(args)>4:
                    meta=args[4]
                    if meta.get('action')=='click' and self.target:
                        w,h=client_size(self.target)
                        self.position_preview.update_step(meta['x'],meta['y'],w,h,meta.get('status','UNKNOWN'))
                    self.state.setText('●  Ejecutando · envío no confirmado')
                    self.session_log.write('VISUAL_STEP',status=meta.get('status'),x=meta.get('x'),y=meta.get('y'))
            elif kind=='ended':
                reason,completed=args
                self.stop()
                self.summary.setText(f'Reproducción: {reason}. Acciones emitidas: {completed}')
    def stop(self):
        if self.running:self.finished_elapsed=time.monotonic()-self.start_time
        self.timer.stop();self.running=False
        self.playback.stop()
        self.session_log.write('GUI_STOP')
        self.overlay.hide()
        self.state.setText("●  Preparado");self.run_button.setText("▶  Iniciar   F6")
    def emergency(self):
        u=ctypes.windll.user32
        held=all(u.GetAsyncKeyState(v)&0x8000 for v in (0x11,0x10,0x7B))
        if held and not self.was_stop:self.stop()
        self.was_stop=held
        record=bool(u.GetAsyncKeyState(0x78)&0x8000)
        pause=bool(u.GetAsyncKeyState(0x79)&0x8000)
        if record and not self.was_record:self.toggle_recording()
        if pause and not self.was_pause:self.toggle_pause_recording()
        self.was_record=record;self.was_pause=pause
    def refresh_stats(self):
        self.counter.setText(str(self.sent))
        sec=max(0,time.monotonic()-self.start_time) if self.running else (getattr(self,'finished_elapsed',0) or 0)
        self.elapsed.setText(f"{int(sec//60):02d}:{sec%60:04.1f}")
        self.rate.setText(f"{self.sent/sec:.1f} / s" if sec else "0 / s")
    def report_error(self,msg):
        QMessageBox.warning(self,"Mouse Virtual",str(msg))
    def toggle_compact(self):
        compact=self.stack.isVisible()
        self.stack.setVisible(not compact)
        self.resize(410 if compact else 1050,550 if compact else 650)
        self.setMinimumWidth(390 if compact else 920)
        self.compact.setText("Expandir" if compact else "▣  Compacto")
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
    def closeEvent(self,event):
        self.tray.hide()
        self.session_log.write('APP_EXIT')
        self.playback.stop()
        self.stop();self.recorder.stop();self.overlay.close();super().closeEvent(event)

def main():
    app=QApplication(sys.argv)
    app.setStyle("Fusion")
    theme=HERE/"theme.qss"
    if theme.exists():app.setStyleSheet(theme.read_text(encoding="utf-8"))
    w=Main();w.show()
    return app.exec()

if __name__=="__main__":sys.exit(main())
