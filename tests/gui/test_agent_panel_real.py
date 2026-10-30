import os,subprocess,sys,time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from mouse_virtual.app.main_window import Main

def test_agent_panel_searches_real_lab_window():
    root=Path(__file__).resolve().parents[2]
    env=os.environ.copy()
    env.pop("QT_QPA_PLATFORM",None)
    fixture=subprocess.Popen([sys.executable,str(root/"scripts/uia_lab/fixture.py")],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    app=QApplication.instance() or QApplication([])
    window=None
    try:
        header=fixture.stdout.readline().strip()
        assert header.startswith("HWND="),header
        hwnd=int(header[5:])
        window=Main()
        window.show_page(5)
        window.agent_windows.clear()
        window.agent_windows.addItem("Laboratorio",hwnd)
        window.agent_id.setEditText("QApplication.QWidget.search_input")
        window.agent_text.setText("perritos")
        window.agent_fill()
        assert "verified" in window.agent_output.toPlainText()
        window.agent_id.setEditText("QApplication.QWidget.search_button")
        window.agent_invoke()
        assert "invoked" in window.agent_output.toPlainText()
        window.agent_type.setCurrentText("Text")
        window.agent_id.setEditText("QApplication.QWidget.search_result")
        for _ in range(20):
            window.agent_read()
            if "Resultados de perritos" in window.agent_output.toPlainText():break
            time.sleep(.1)
        assert "Resultados de perritos" in window.agent_output.toPlainText()
    finally:
        if window:window.close()
        fixture.terminate()
        try:fixture.wait(timeout=3)
        except subprocess.TimeoutExpired:fixture.kill();fixture.wait(timeout=3)
