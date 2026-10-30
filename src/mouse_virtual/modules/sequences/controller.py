"""Mouse Virtual desktop module."""
from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem
from mouse_virtual.modules.sequences.models import Plan, Step
from mouse_virtual.app.ui_helpers import btn, label, spin

class SequencesMixin:

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

    def transfer_recording(self):
        self.recorder.stop();self.poll_recording()
        if not self.recorded:
            self.report_error('No hay clics grabados para transferir.');return
        if not self.selected_sequence_id:self.save_recording_as_sequence()
        self.show_page(2)

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

