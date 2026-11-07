"""Real Chromium MV3 + CDP test on a NON-ACTIVE tab, never user's Chrome.

Runs with a temporary profile in headless mode. Demonstrates that the extension
performs targeted pointer/text input without activating its tab.
"""
import asyncio
import base64
import json
import os
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
        try:
            async with websockets.serve(bridge.handler, "127.0.0.1", 8765,
                                         max_size=8 * 1024 * 1024):
                async with playwright.async_playwright() as pw:
                    with tempfile.TemporaryDirectory(prefix="mv-ext-test-") as profile:
                        ctx = await pw.chromium.launch_persistent_context(
                            user_data_dir=profile, channel="chromium", headless=True,
                            args=["--disable-extensions-except=" + str(EXT),
                                  "--load-extension=" + str(EXT)],
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
                            outcome = await send_commands(TOKEN, sequence, 8765)
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
                            await worker.evaluate("detach()")
                        finally:
                            await ctx.close()
        finally:
            http.shutdown()
            http.server_close()
            thread.join(2)
    asyncio.run(run())
