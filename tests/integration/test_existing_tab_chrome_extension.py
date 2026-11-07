"""Real Chromium MV3 + CDP test on a NON-ACTIVE tab, never user's Chrome.

Runs with a temporary profile in headless mode. Demonstrates that the extension
performs targeted pointer/text input without activating its tab.
"""
import asyncio
import base64
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from mouse_virtual.modules.agent_control.tab_bridge import TabBridge, send_commands

playwright = pytest.importorskip("playwright.async_api")
websockets = pytest.importorskip("websockets.asyncio.server")

EXT = Path(__file__).resolve().parents[2] / "src/mouse_virtual/infrastructure/browser/existing_tab_extension"
TOKEN = "e" * 64
HTML = """<html><head><title>Fixture</title></head><body>
<input id="name"><input id="media" type="file"><button id="save"
onclick="document.querySelector('#result').textContent='Confirmed: '+
document.querySelector('#name').value">Save</button><span id="result"></span>
</body></html>"""


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def test_actual_background_tab_mouse_and_typing():
    async def run():
        http = HTTPServer(("127.0.0.1", 0), FixtureHandler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        address = f"http://127.0.0.1:{http.server_port}/"
        bridge = TabBridge(TOKEN)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port=probe.getsockname()[1]
        try:
            async with websockets.serve(bridge.handler, "127.0.0.1", port,
                                         max_size=8 * 1024 * 1024):
                async with playwright.async_playwright() as pw:
                    # Avoid placing private screenshots beneath the Git checkout,
                    # even if pytest temporarily overrides the TMP environment.
                    external_tmp=Path.home()/".mouse-virtual-test-temp"
                    external_tmp.mkdir(parents=True,exist_ok=True)
                    with tempfile.TemporaryDirectory(prefix="mv-ext-test-",
                                                     dir=str(external_tmp)) as profile:
                        custom_ext=Path(profile)/"extension"
                        shutil.copytree(EXT,custom_ext)
                        for name in ("worker.js","manifest.json"):
                            f=custom_ext/name
                            f.write_text(f.read_text("utf8").replace(
                                "ws://127.0.0.1:8765",
                                f"ws://127.0.0.1:{port}"),encoding="utf8")
                        ctx = await pw.chromium.launch_persistent_context(
                            user_data_dir=str(Path(profile)/"browser"), channel="chromium", headless=True,
                            args=["--disable-extensions-except=" + str(custom_ext),
                                  "--load-extension=" + str(custom_ext)],
                            viewport={"width": 700, "height": 550},
                        )
                        try:
                            worker = ctx.service_workers[0] if ctx.service_workers else \
                                await ctx.wait_for_event("serviceworker", timeout=15000)
                            other = await ctx.new_page()
                            await other.goto(address)
                            target = await ctx.new_page()
                            await target.goto(address)
                            await other.bring_to_front()
                            paired = await worker.evaluate("""async ({url,token}) => {
                              const tabs=await chrome.tabs.query({});
                              const tab=tabs.find(t=>t.url?.startsWith(url)&&!t.active);
                              if(!tab)throw Error('Background tab unavailable');
                              return await attach(tab.id,token);
                            }""", {"url": address, "token": TOKEN})
                            assert paired["ok"], paired
                            video=Path(profile)/"demo.mp4"
                            video.write_bytes(b"local-video-fixture-data")
                            sequence = [
                                {"action": "navigate", "url": address},
                                {"action": "move", "x": 100, "y": 100},
                                {"action": "dom.fill", "selector": "#name", "text": "hello"},
                                {"action": "dom.click", "selector": "#save"},
                                {"action": "file", "selector": "#media", "path": str(video)},
                                {"action": "screenshot"},
                            ]
                            outcome = await send_commands(TOKEN, sequence, port)
                            assert len(outcome) == len(sequence)
                            assert all(x["result"]["ok"] for x in outcome), outcome
                            assert base64.b64decode(outcome[-1]["result"]["data"]).startswith(b"\x89PNG\r\n\x1a\n")
                            # Prove that a separate local controller can save a
                            # background-tab screenshot outside the source tree.
                            token_file=Path(profile)/"pairing.key"
                            token_file.write_text(TOKEN)
                            plan_file=Path(profile)/"capture.json"
                            plan_file.write_text(json.dumps([{"action":"screenshot"}]))
                            snapshot=Path(profile)/"background.png"
                            env=os.environ.copy()
                            env["PYTHONPATH"]=str(Path(__file__).resolve().parents[2]/"src")
                            proc=await asyncio.create_subprocess_exec(
                                sys.executable,"-m","mouse_virtual.modules.agent_control.tab_bridge",
                                "run","--token-file",str(token_file),
                                "--plan",str(plan_file),"--screenshot-output",str(snapshot),
                                "--port",str(port),
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,env=env)
                            stdout,stderr=await proc.communicate()
                            assert proc.returncode==0,(stdout.decode(errors="replace"),stderr.decode(errors="replace"))
                            assert snapshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
                            assert await target.locator("#result").inner_text() == "Confirmed: hello"
                            assert await target.locator("#media").evaluate("(el)=>el.files?.[0]?.name") == "demo.mp4"
                            assert await other.locator("#result").inner_text() == ""
                            state = await worker.evaluate("""async () => ({
                              active:(await chrome.tabs.query({active:true,currentWindow:true}))[0].id,
                              attached:targetId
                            })""")
                            assert state["active"] != state["attached"], state
                            original_id=state["attached"]
                            # Create two tabs in an actual Chrome tab group, no
                            # foreground activation or change to other tab.
                            created=await send_commands(TOKEN,[
                                {"action":"workspace.create","url":address}],port)
                            assert created[0]["result"]["ok"],created
                            first=created[0]["result"]["tab"]["tabId"]
                            group=created[0]["result"]["groupId"]
                            opened=await send_commands(TOKEN,[
                                {"action":"workspace.open","url":address}],port)
                            assert opened[0]["result"]["ok"],opened
                            second=opened[0]["result"]["tab"]["tabId"]
                            assert opened[0]["result"]["groupId"]==group
                            listed=await send_commands(TOKEN,[{"action":"tab.list"}],port)
                            assert listed[0]["result"]["ok"],listed
                            assert {first,second}.issubset({
                                t["tabId"] for t in listed[0]["result"]["workspace"]["tabs"]
                            })
                            selected=await send_commands(TOKEN,[
                                {"action":"workspace.select","tabId":first}],port)
                            assert selected[0]["result"]["ok"],selected
                            payload=await send_commands(TOKEN,[
                                {"action":"dom.fill","selector":"#name","text":"workspace"},
                                {"action":"dom.click","selector":"#save"}],port)
                            assert all(z["result"]["ok"] for z in payload),payload
                            # No user-facing page is changed by workspace actions.
                            assert await other.locator("#result").inner_text()==""
                            outside=await send_commands(TOKEN,[
                                {"action":"tab.select_id","tabId":original_id,
                                 "host":"127.0.0.1"}],port)
                            assert outside[0]["result"]["ok"],outside
                            again=await send_commands(TOKEN,[
                                {"action":"workspace.select","tabId":first}],port)
                            assert again[0]["result"]["ok"],again
                            after=await worker.evaluate("""async () => ({
                              active:(await chrome.tabs.query({active:true,currentWindow:true}))[0].id,
                              attached:targetId
                            })""")
                            assert after["active"]!=after["attached"],after
                            closed=await send_commands(TOKEN,[
                                {"action":"workspace.close","tabId":second}],port)
                            assert closed[0]["result"]["ok"],closed
                            await worker.evaluate("disconnect()")
                        finally:
                            await ctx.close()
        finally:
            http.shutdown()
            http.server_close()
            thread.join(2)
    asyncio.run(run())
