from PySide6.QtWidgets import QApplication
from mouse_virtual.app.main_window import Main
from mouse_virtual.modules.agent_control import controller as agent_panel
from mouse_virtual.modules.automation import controller as automation

def test_sixth_tab_contains_agent_controls():
    app=QApplication.instance() or QApplication([])
    window=Main()
    try:
        assert len(window.tabs)==7
        assert window.tabs[6].text()=="Pestaña existente"
        window.show_page(5)
        assert window.mode=="agent"
        assert window.agent_windows.objectName()=="agentWindows"
        assert window.agent_output.isReadOnly()
    finally:window.close()

def test_agent_panel_requires_explicit_target(monkeypatch):
    app=QApplication.instance() or QApplication([])
    window=Main()
    try:
        window.show_page(5)
        window.agent_windows.clear()
        window.agent_id.setEditText("search_input")
        window.agent_text.setText("perritos")
        window.agent_fill()
        assert "Selecciona una ventana" in window.agent_output.toPlainText()
    finally:window.close()

def test_agent_panel_dispatches_explicit_command(monkeypatch):
    app=QApplication.instance() or QApplication([])
    window=Main()
    try:
        window.show_page(5)
        window.agent_windows.clear()
        window.agent_windows.addItem("Laboratorio",2020)
        window.agent_id.setEditText("search_input")
        window.agent_text.setText("perritos")
        calls=[]
        class FakeExecutor:
            def execute(self,command):
                calls.append(command)
                return {"verified":True}
        monkeypatch.setattr(agent_panel,"DesktopExecutor",lambda hwnd:object())
        monkeypatch.setattr(agent_panel,"AgentExecutor",lambda desktop:FakeExecutor())
        window.agent_fill()
        assert calls[0].action=="desktop.fill"
        assert calls[0].auto_id=="search_input"
        assert calls[0].text=="perritos"
        assert "verified" in window.agent_output.toPlainText()
    finally:window.close()
