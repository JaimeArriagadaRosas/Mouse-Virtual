from .commands import Command
class AgentExecutor:
    def __init__(self,browser=None,desktop=None):
        self.browser=browser
        self.desktop=desktop
    def execute(self,command:Command):
        command.validate()
        a=command.action
        if a.startswith("desktop."):
            if self.desktop is None:raise RuntimeError("Desktop session not connected")
            return self.desktop.execute(command)
        if a=="browser.open":return self.browser.open(command.url)
        if a=="browser.find_element":return {"found":self.browser.locate(command.role,command.name).count()>0}
        if a=="browser.fill":return self.browser.fill(command.text,command.role,command.name)
        if a=="browser.click":return self.browser.click(command.role,command.name)
        if a=="browser.read_page":return self.browser.read_page()
        if a=="browser.search":
            self.browser.fill(command.query,command.role or "searchbox",command.name or "Buscar")
            self.browser.locate("button","Buscar").click()
            return self.browser.read_page()
        raise ValueError("Unsupported action")
