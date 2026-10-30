"""Mouse Virtual desktop module."""
import ctypes
import time
from PySide6.QtWidgets import QMessageBox
from mouse_virtual.infrastructure.geometry import compare, snapshot
from mouse_virtual.infrastructure.windows.handles import client_size, client_to_screen
from mouse_virtual.infrastructure.windows.input import native_click, native_key, post_click
from mouse_virtual.modules.recording.recorder import active_window, window_info
from mouse_virtual.modules.sequences.models import Plan, Step
from mouse_virtual.app.ui_helpers import choice

class PlaybackMixin:
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
        self.state.setText("●  Preparado");self.run_button.setText("▶  Iniciar   F6")

    def refresh_stats(self):
        self.counter.setText(str(self.sent))
        sec=max(0,time.monotonic()-self.start_time) if self.running else (getattr(self,'finished_elapsed',0) or 0)
        self.elapsed.setText(f"{int(sec//60):02d}:{sec%60:04.1f}")
        self.rate.setText(f"{self.sent/sec:.1f} / s" if sec else "0 / s")

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

