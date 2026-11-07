"""Local-only, explicitly paired transport for controlling an ALREADY OPEN Chrome tab.

The Chrome extension attaches to the selected existing tab; no new Chrome profile,
foreground mouse movement, SendInput, or global keystrokes are used.

This module does not read browser cookies or store accounts/URLs in Git.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hmac
import json
import secrets
import sys
from pathlib import Path
from urllib.parse import urlparse

from mouse_virtual.modules.agent_control.browser_workflows import approved_upload_path

PORT = 8765
MAX_MESSAGE = 20 * 1024 * 1024
from mouse_virtual.modules.agent_control.tab_validators import (
    READ_ACTIONS, WRITE_ACTIONS, ACTIONS, KEYS, load_token, validate_command,
)

class TabBridge:
    def __init__(self, token: str):
        self.token = token
        self.extension = None
        self.tab_id = None
        self.pending: dict[str, asyncio.Future] = {}
        self.busy = asyncio.Lock()

    async def handler(self, ws):
        origin = ws.request.headers.get("Origin", "")
        try:
            raw = await asyncio.wait_for(ws.recv(), 10)
            data = json.loads(raw)
            role = data.get("role")
            token = data.get("token", "")
            if not isinstance(token, str) or not hmac.compare_digest(token, self.token):
                await ws.close(code=1008, reason="Unauthorized")
                return
            if role == "extension":
                # Only locally installed Chrome extensions may register.
                if not origin.startswith("chrome-extension://"):
                    await ws.close(code=1008, reason="Extension origin required")
                    return
                if self.extension is not None and self.extension != ws:
                    await ws.close(code=1008, reason="Tab is already paired")
                    return
                tid = data.get("tabId")
                if type(tid) is not int or tid <= 0:
                    await ws.close(code=1008, reason="Invalid tab ID")
                    return
                self.extension, self.tab_id = ws, tid
                await ws.send(json.dumps({"ok": True, "role": role}))
                try:
                    async for raw in ws:
                        reply = json.loads(raw)
                        if reply.get("kind") == "heartbeat":
                            await ws.send(json.dumps({"kind": "heartbeat_ack"}))
                        elif reply.get("kind") == "tab_changed":
                            changed = reply.get("tabId")
                            if type(changed) is int and changed > 0:
                                self.tab_id = changed
                        elif reply.get("kind") == "reply":
                            fid = reply.get("id")
                            fut = self.pending.pop(fid, None)
                            if fut and not fut.done():
                                fut.set_result(reply)
                finally:
                    self.extension, self.tab_id = None, None
                    for f in self.pending.values():
                        if not f.done():
                            f.set_exception(ConnectionError("Browser tab connection lost"))
                    self.pending.clear()
            elif role == "controller":
                if origin:
                    await ws.close(code=1008, reason="Controller is local CLI only")
                    return
                await ws.send(json.dumps({"ok": True, "role": role}))
                async for raw in ws:
                    call = {}
                    try:
                        call = json.loads(raw)
                        fid = call.get("id")
                        action = call.get("action")
                        if type(fid) is not str or not (1 <= len(fid) <= 80):
                            raise ValueError("Invalid request ID")
                        if action == "status":
                            payload = {"ok": True, "connected": self.extension is not None,
                                       "tab_id": self.tab_id}
                        elif action not in ACTIONS:
                            raise ValueError("Invalid action")
                        else:
                            if not self.extension:
                                raise ConnectionError("No paired browser tab")
                            async with self.busy:
                                future = asyncio.get_running_loop().create_future()
                                self.pending[fid] = future
                                try:
                                    await self.extension.send(json.dumps(call))
                                    payload = await asyncio.wait_for(future, timeout=25)
                                finally:
                                    self.pending.pop(fid, None)
                        await ws.send(json.dumps({"id": fid, "result": payload}))
                    except Exception as exc:
                        await ws.send(json.dumps({"id": call.get("id") if
                            isinstance(call, dict) else None, "result": {"ok": False,
                            "error_type": type(exc).__name__, "error": str(exc)[:250],
                            "retry_safe": False}}))
            else:
                await ws.close(code=1008, reason="Unknown role")
        except (OSError, ValueError, json.JSONDecodeError, asyncio.TimeoutError):
            await ws.close(code=1008, reason="Invalid handshake")


async def serve_bridge(token, port=PORT):
    from websockets.asyncio.server import serve
    bridge = TabBridge(token)
    async with serve(bridge.handler, "127.0.0.1", port,
                     max_size=MAX_MESSAGE, ping_interval=20):
        print(json.dumps({"ready": True, "listen": "127.0.0.1",
                          "port": port, "auth": "required", "token_printed": False}),
              flush=True)
        await asyncio.Future()


async def send_commands(token, commands, port=PORT):
    from websockets.asyncio.client import connect
    results = []
    async with connect(f"ws://127.0.0.1:{port}", max_size=MAX_MESSAGE,
                       open_timeout=5) as ws:
        await ws.send(json.dumps({"role": "controller", "token": token}))
        hello = json.loads(await asyncio.wait_for(ws.recv(), 8))
        if not hello.get("ok"):
            raise PermissionError("Tab bridge rejected the controller")
        for index, item in enumerate(commands):
            request = {"id": secrets.token_hex(8), **item}
            await ws.send(json.dumps(request, ensure_ascii=False))
            reply = json.loads(await asyncio.wait_for(ws.recv(), 30))
            result = reply.get("result", {})
            results.append({"index": index, "action": item["action"], "result": result})
            if not result.get("ok"):
                break
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Operate an existing Chrome tab without OS mouse input")
    sub = parser.add_subparsers(dest="mode", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--token-file", type=Path, required=True)
    s.add_argument("--port", type=int, default=PORT)
    r = sub.add_parser("run")
    r.add_argument("--token-file", type=Path, required=True)
    r.add_argument("--plan", type=Path, required=True)
    r.add_argument("--allow-host", action="append", default=[])
    r.add_argument("--allow-file-root", action="append", default=[])
    r.add_argument("--allow-writes", action="store_true")
    r.add_argument("--screenshot-output", type=Path,
                   help="Save captured page PNG outside the public source tree")
    r.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args(argv)
    try:
        token = load_token(args.token_file, create=args.mode == "serve")
        if args.mode == "serve":
            asyncio.run(serve_bridge(token, args.port))
            return 0
        source = args.plan.resolve(strict=True)
        if source.stat().st_size > 65536:
            raise ValueError("Plan larger than 64 KiB")
        steps = json.loads(source.read_text(encoding="utf-8"))
        if type(steps) is not list or not 1 <= len(steps) <= 40:
            raise ValueError("Plan must be a list of 1..40 commands")
        normalized = [validate_command(s, allow_writes=args.allow_writes,
                        allow_hosts=args.allow_host, file_roots=args.allow_file_root)
                      for s in steps]
        response = asyncio.run(send_commands(token, normalized, args.port))
        for entry in response:
            if entry["action"] == "screenshot" and entry["result"].get("data"):
                binary = base64.b64decode(entry["result"].pop("data"), validate=True)
                if not binary.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError("Invalid screenshot payload")
                entry["result"]["image_size_bytes"] = len(binary)
                if args.screenshot_output:
                    target = args.screenshot_output.expanduser().resolve()
                    source_tree = Path(__file__).resolve().parents[4]
                    if target.is_relative_to(source_tree) or target.suffix.lower() != ".png":
                        raise PermissionError("Screenshot must be PNG outside the source repository")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as out:
                        out.write(binary)
                    entry["result"]["saved_path"] = str(target)
        print(json.dumps(response, ensure_ascii=False), flush=True)
        return 0 if len(response) == len(normalized) and all(
            item["result"].get("ok") for item in response) else 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error_type": type(exc).__name__,
                          "error": str(exc)[:250]}), file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
