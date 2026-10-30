"""Mouse Virtual desktop module."""
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QMenu, QSystemTrayIcon
from mouse_virtual.modules.playback.engine import Playback, SessionLog
from mouse_virtual.modules.recording.recorder import MouseRecorder
from mouse_virtual.modules.sequences.repository import SequenceStore


from mouse_virtual.modules.clicker.controller import ClickerMixin
from mouse_virtual.modules.agent_control.controller import AgentPanelMixin
from mouse_virtual.modules.keyboard.controller import KeyboardMixin
from mouse_virtual.modules.sequences.controller import SequencesMixin
from mouse_virtual.modules.sequences.view import SequencePageMixin
from mouse_virtual.modules.recording.controller import RecordingMixin
from mouse_virtual.modules.playback.controller import PlaybackMixin
from mouse_virtual.modules.virtual_cursor.controller import VirtualCursorMixin
from mouse_virtual.modules.automation.controller import AutomationMixin
from mouse_virtual.app.settings_controller import SettingsMixin
from mouse_virtual.app.ui_layout import LayoutMixin

class Main(AgentPanelMixin, ClickerMixin, KeyboardMixin, SequencePageMixin, SequencesMixin, RecordingMixin, PlaybackMixin, VirtualCursorMixin, AutomationMixin, SettingsMixin, LayoutMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Virtual")
        self.resize(1450,875);self.setMinimumSize(1010,675)
        self.setObjectName("window")
        self.running=False;self.sent=0;self.start_time=0;self.target=None
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
        self.agent_refresh_windows()
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
    def closeEvent(self,event):
        self.tray.hide()
        self.session_log.write('APP_EXIT')
        self.playback.stop()
        self.stop();self.recorder.stop();super().closeEvent(event)
