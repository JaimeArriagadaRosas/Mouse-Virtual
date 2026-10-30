from mouse_virtual.modules.agent_control.commands import Command
from mouse_virtual.modules.agent_control.executor import AgentExecutor
import pytest
class FakeElement:
    def count(self):return 1
    def click(self):pass
class FakeBrowser:
    def __init__(self):self.actions=[]
    def open(self,url):self.actions.append(("open",url));return {"url":url}
    def locate(self,role="",name=""):self.actions.append(("locate",role,name));return FakeElement()
    def fill(self,text,role="",name=""):self.actions.append(("fill",text,role,name));return {"filled":True}
    def read_page(self):return {"text":"Resultados de perritos"}
def test_search_flow():
    b=FakeBrowser();result=AgentExecutor(b).execute(Command("browser.search",query="perritos"))
    assert result["text"]=="Resultados de perritos"
    assert b.actions==[("fill","perritos","searchbox","Buscar"),("locate","button","Buscar")]
def test_reject_unknown_actions_and_schemes():
    with pytest.raises(ValueError):Command("shell.exec").validate()
    with pytest.raises(ValueError):Command("browser.open",url="file:///etc/passwd").validate()
def test_field_discovery():
    assert AgentExecutor(FakeBrowser()).execute(Command("browser.find_element",role="textbox",name="Buscar"))["found"]
