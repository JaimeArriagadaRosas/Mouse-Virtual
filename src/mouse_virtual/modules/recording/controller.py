"""Mouse Virtual desktop module."""
from PySide6.QtWidgets import QTableWidgetItem
from mouse_virtual.infrastructure.geometry import snapshot
from mouse_virtual.modules.recording.recorder import window_info

class RecordingMixin:
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

