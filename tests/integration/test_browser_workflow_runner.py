"""End-to-end browser workflow on a LOCAL ephemeral HTTP server only."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import os
import subprocess
import sys
import threading

import pytest

from mouse_virtual.modules.agent_control.browser_workflows import execute_plan

HTML = """<!doctype html><html><head><title>Independent demo</title></head><body>
<label for="query">Question</label><input id="query" aria-label="Question">
<input type="file" id="media-upload" aria-label="Media upload">
<button onclick="document.getElementById('result').textContent='Found: '+
document.getElementById('query').value">Search</button>
<div role="status" aria-label="Outcome" id="result"></div>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        raw = HTML.encode("utf8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


@pytest.fixture
def site():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        t.join(2)


def test_real_headless_workflow_isolated(site, tmp_path):
    pytest.importorskip("playwright")
    plan = {"version": 1, "name": "Independent browser",
            "steps": [
                {"action": "open", "url": site},
                {"action": "fill", "role": "textbox", "name": "Question", "value": "example"},
                {"action": "click", "role": "button", "name": "Search"},
                {"action": "assert_text", "role": "status", "name": "Outcome",
                 "contains": "Found: example"},
                {"action": "screenshot", "name": "finished"},
            ]}
    result = execute_plan(plan, allowed_hosts={"127.0.0.1"}, allow_writes=True,
                          artifacts_dir=tmp_path, headless=True)
    assert result["ok"] and result["completed"] == 5
    assert (tmp_path / "finished.png").stat().st_size > 1000


def test_cli_dry_run_reports_without_launch(site, tmp_path):
    plan = {"version": 1, "steps": [
        {"action": "open", "url": site},
        {"action": "fill", "role": "textbox", "name": "Question", "value": "example"},
    ]}
    f = tmp_path / "plan.json"
    f.write_text(json.dumps(plan))
    cmd = [sys.executable, "-m",
           "mouse_virtual.modules.agent_control.browser_workflow_cli",
           "--plan", str(f), "--allow-host", "127.0.0.1", "--dry-run"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["writes_requested"] is True
    assert payload["step_count"] == 2


def test_headless_file_attachment_uses_file_root(site, tmp_path):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"fictional-video-data" * 90)
    plan = {"version": 1, "steps": [
        {"action": "open", "url": site},
        {"action": "upload_file", "path": str(media), "index": 0},
    ]}
    response = execute_plan(plan, allowed_hosts={"127.0.0.1"},
                            allowed_file_roots=[tmp_path], allow_writes=True,
                            headless=True)
    assert response["ok"] and response["completed"] == 2
    assert response["steps"][-1]["result"]["bytes"] == media.stat().st_size
