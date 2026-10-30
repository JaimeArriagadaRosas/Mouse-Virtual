"""Exercise the agent CLI from a separate process with an isolated local web server."""
from http.server import BaseHTTPRequestHandler,HTTPServer
import json,os,subprocess,sys,threading
from pathlib import Path
class Web(BaseHTTPRequestHandler):
    def do_GET(self):
        html="""<html><head><title>Prueba CLI</title></head><body>
        <input type="search" role="searchbox" aria-label="Buscar" id="q">
        <button onclick="document.getElementById('r').textContent='Resultados de '+document.getElementById('q').value">Buscar</button>
        <div id="r"></div></body></html>"""
        data=html.encode()
        self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(data)));self.end_headers()
        self.wfile.write(data)
    def log_message(self,*args):pass

def test_cli_search_works_outside_current_process():
    root=Path(__file__).resolve().parents[2]
    server=HTTPServer(("127.0.0.1",0),Web)
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    try:
        env=os.environ.copy()
        env["PYTHONPATH"]=str(root/"src")
        cmd=[sys.executable,"-m","mouse_virtual.modules.agent_control.cli",
             "--url",f"http://127.0.0.1:{server.server_port}",
             "--allowed-host","127.0.0.1","--query","perritos"]
        result=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True,timeout=25)
        assert result.returncode==0,result.stderr
        payload=json.loads(result.stdout)
        assert payload["ok"] is True
        assert "Resultados de perritos" in payload["result"]["text"]
    finally:
        server.shutdown();server.server_close();t.join(2)
