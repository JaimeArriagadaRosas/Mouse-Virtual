"""Application UI adapter for explicitly scoped UI Automation actions."""
import json
from mouse_virtual.infrastructure.windows.handles import windows
from mouse_virtual.modules.agent_control.view import build_agent_page
from mouse_virtual.modules.agent_control.desktop import DesktopExecutor
from mouse_virtual.modules.agent_control.commands import Command
from mouse_virtual.modules.agent_control.executor import AgentExecutor

class AgentPanelMixin:
    def agent_page(self):
        return build_agent_page(self)

    def agent_refresh_windows(self):
        previous=self.agent_windows.currentData()
        self.agent_windows.clear()
        for hwnd,title in windows():
            if "Mouse Virtual" not in title and "MouseVirtual" not in title:
                self.agent_windows.addItem(f"{title} (HWND {hwnd})",int(hwnd))
        index=self.agent_windows.findData(previous)
        if index>=0:self.agent_windows.setCurrentIndex(index)

    def _agent_executor(self):
        hwnd=self.agent_windows.currentData()
        if not hwnd:
            raise ValueError("Selecciona una ventana destino.")
        return AgentExecutor(desktop=DesktopExecutor(int(hwnd)))

    def _agent_run(self,action,*,control_type=None,text=None):
        try:
            control_id=self.agent_id.currentText().strip()
            if not control_id:
                raise ValueError("Indica o selecciona un AutomationId.")
            command=Command(action,auto_id=control_id,
                            control_type=control_type or self.agent_type.currentText(),
                            text=self.agent_text.text() if text is None else text)
            result=self._agent_executor().execute(command)
            self.agent_output.appendPlainText(json.dumps({"action":action,"result":result},ensure_ascii=False))
            return result
        except Exception as exc:
            self.agent_output.appendPlainText(json.dumps({"action":action,"error":str(exc)},ensure_ascii=False))
            return None

    def agent_inspect(self):
        try:
            executor=self._agent_executor()
            root=executor.desktop.session.root
            data=[]
            for item in root.descendants():
                info=item.element_info
                if getattr(info,"control_type","") not in ("Edit","Button","Text"):
                    continue
                auto_id=getattr(info,"automation_id","")
                if not auto_id:continue
                data.append({"id":auto_id,"type":info.control_type,"name":item.window_text()[:100]})
            self.agent_id.clear()
            self.agent_id.addItems([x["id"] for x in data])
            self.agent_output.setPlainText(json.dumps({"controls":data[:100]},ensure_ascii=False,indent=2))
        except Exception as exc:
            self.agent_output.appendPlainText("Error de inspección: "+str(exc))

    def agent_fill(self):
        self._agent_run("desktop.fill",control_type="Edit")

    def agent_invoke(self):
        self._agent_run("desktop.invoke",control_type="Button")

    def agent_read(self):
        self._agent_run("desktop.read_control")
