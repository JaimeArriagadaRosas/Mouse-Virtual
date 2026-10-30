"""Browser integration test: isolated localhost fixture, no external network or OS input."""
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from mouse_virtual.infrastructure.browser.session import BrowserSession
from mouse_virtual.modules.agent_control.executor import AgentExecutor
from mouse_virtual.modules.agent_control.commands import Command
import pytest

HTML = """<!doctype html><html lang="es"><head><title>Laboratorio de búsqueda</title></head>
<body><h1>Buscador de laboratorio</h1>
<form onsubmit="event.preventDefault();document.querySelector('#result').textContent='Resultados de '+document.querySelector('#query').value;">
<label for="query">Buscar</label><input id="query" type="search" role="searchbox" aria-label="Buscar">
<button type="submit">Buscar</button></form><div id="result"></div></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data=HTML.encode("utf-8")
        self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
    def log_message(self,*args):pass

@pytest.fixture
def local_search():
    httpd=HTTPServer(("127.0.0.1",0),Handler)
    thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
    yield "http://127.0.0.1:"+str(httpd.server_port)
    httpd.shutdown();httpd.server_close();thread.join(2)

def test_real_browser_search_perritos(local_search):
    with BrowserSession(allowed_hosts={"127.0.0.1"}) as browser:
        executor=AgentExecutor(browser)
        opened=executor.execute(Command("browser.open",url=local_search))
        assert opened["title"]=="Laboratorio de búsqueda"
        assert executor.execute(Command("browser.find_element",role="searchbox",name="Buscar"))["found"]
        result=executor.execute(Command("browser.search",query="perritos"))
        assert "Resultados de perritos" in result["text"]
        assert browser.page.locator("#query").input_value()=="perritos"
def test_browser_host_rejected_without_navigation():
    session=BrowserSession(allowed_hosts={"127.0.0.1"})
    with pytest.raises(PermissionError):
        session.open("https://example.com")
