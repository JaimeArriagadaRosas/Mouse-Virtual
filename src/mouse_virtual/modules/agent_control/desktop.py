"""Scoped desktop automation actions, no global keyboard fallback."""
from mouse_virtual.infrastructure.windows.accessibility import AccessibilitySession

class DesktopExecutor:
    def __init__(self, hwnd, session_factory=AccessibilitySession):
        self.session=session_factory(hwnd).connect()
    def execute(self,command):
        command.validate()
        if command.action=="desktop.find_control":
            found=self.session.find(auto_id=command.auto_id,name=command.name,control_type=command.control_type)
            return {"found":True,"name":found.window_text()}
        if command.action=="desktop.fill":
            return self.session.fill(command.text,auto_id=command.auto_id,name=command.name)
        if command.action=="desktop.invoke":
            return self.session.invoke(auto_id=command.auto_id,name=command.name)
        if command.action=="desktop.read_control":
            return self.session.read(auto_id=command.auto_id,name=command.name,control_type=command.control_type)
        raise ValueError("Unsupported desktop action")
