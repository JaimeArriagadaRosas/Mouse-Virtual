"""Regression tests for scoped existing-tab transport; no user browser required."""
import asyncio
import json
import secrets
from pathlib import Path

import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from mouse_virtual.modules.agent_control.tab_bridge import (
    TabBridge, load_token, validate_command, send_commands,
)

SECRET = "a" * 64


def test_pairing_token_generated_outside_source(tmp_path):
    path = tmp_path / "private" / "pairing.key"
    token = load_token(path, create=True)
    assert len(token) == 64
    assert load_token(path) == token
    assert SECRET != token
    assert path.read_text() == token


def test_commands_validate_write_and_explicit_hosts(tmp_path):
    with pytest.raises(PermissionError):
        validate_command({"action": "click", "x": 30, "y": 40})
    assert validate_command({"action": "click", "x": 30, "y": 40},
                            allow_writes=True)["x"] == 30
    with pytest.raises(PermissionError):
        validate_command({"action": "navigate", "url": "https://example.com"},
                         allow_writes=True)
    assert validate_command({"action": "navigate", "url": "https://example.com"},
                            allow_writes=True, allow_hosts=["example.com"])
    with pytest.raises(ValueError):
        validate_command({"action": "navigate", "url": "file:///etc/hosts"},
                         allow_writes=True, allow_hosts=["example.com"])
    with pytest.raises(ValueError):
        validate_command({"action": "type", "text": "x", "shell": "whoami"},
                         allow_writes=True)
    with pytest.raises(ValueError):
        validate_command({"action": "move", "x": -1, "y": 23},
                         allow_writes=True)


def test_file_requires_explicit_root(tmp_path):
    file = tmp_path / "video.mp4"
    file.write_bytes(b"video")
    req = {"action": "file", "selector": "input[type=file]", "path": str(file)}
    with pytest.raises(PermissionError):
        validate_command(req, allow_writes=True)
    accepted = validate_command(req, allow_writes=True, file_roots=[tmp_path])
    assert Path(accepted["path"]) == file
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    with pytest.raises(PermissionError):
        validate_command(req, allow_writes=True, file_roots=[elsewhere])


def test_bridge_forwards_to_only_paired_extension():
    async def run():
        token = SECRET
        bridge = TabBridge(token)
        async with serve(bridge.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            # Initially there is no tab connection.
            status = await send_commands(token, [{"action": "status"}], port)
            assert status[0]["result"]["connected"] is False

            async with connect(f"ws://127.0.0.1:{port}",
                               origin="chrome-extension://unit-test") as ext:
                await ext.send(json.dumps({"role": "extension", "token": token,
                                           "tabId": 515}))
                ack = json.loads(await ext.recv())
                assert ack == {"ok": True, "role": "extension"}

                async def emulate_target():
                    raw = json.loads(await ext.recv())
                    assert raw["action"] == "click"
                    assert raw["x"] == 10
                    await ext.send(json.dumps({"kind": "reply", "id": raw["id"],
                                               "ok": True, "clicked": True}))
                actor = asyncio.create_task(emulate_target())
                commands = await send_commands(token, [
                    {"action": "status"}, {"action": "click", "x": 10, "y": 22}
                ], port)
                await actor
                assert commands[0]["result"]["connected"] is True
                assert commands[0]["result"]["tab_id"] == 515
                assert commands[1]["result"]["ok"] is True
                assert commands[1]["result"]["clicked"] is True

            await asyncio.sleep(.05)
            assert bridge.extension is None
    asyncio.run(run())


def test_bridge_rejects_wrong_token_and_non_extension_origin():
    async def run():
        bridge = TabBridge(SECRET)
        async with serve(bridge.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect(f"ws://127.0.0.1:{port}",
                               origin="https://untrusted.example") as ext:
                await ext.send(json.dumps({"role": "extension", "token": SECRET,
                                           "tabId": 4}))
                with pytest.raises(Exception):
                    await ext.recv()
            assert bridge.extension is None
            async with connect(f"ws://127.0.0.1:{port}") as controller:
                await controller.send(json.dumps({"role": "controller",
                                                  "token": "bad"}))
                with pytest.raises(Exception):
                    await controller.recv()
    asyncio.run(run())


def test_switch_tab_requires_explicit_host_permission():
    request = {"action": "tab.select", "host": "example.net"}
    with pytest.raises(PermissionError):
        validate_command(request, allow_writes=True, allow_hosts=["example.com"])
    assert validate_command(request, allow_writes=True, allow_hosts=["example.net"]) == request
    with pytest.raises(PermissionError):
        validate_command(request, allow_writes=False, allow_hosts=["example.net"])
    with pytest.raises(ValueError):
        validate_command({"action": "tab.select", "host": "example.net",
                          "urlPrefix": "https://example.com/private"},
                         allow_writes=True, allow_hosts=["example.net"])


def test_bridge_heartbeats_and_selected_tab_status():
    async def run():
        bridge = TabBridge(SECRET)
        async with serve(bridge.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect(f"ws://127.0.0.1:{port}",
                               origin="chrome-extension://unit-test") as ext:
                await ext.send(json.dumps({"role":"extension","token":SECRET,"tabId":400}))
                assert json.loads(await ext.recv())["ok"]
                await ext.send(json.dumps({"kind":"heartbeat"}))
                assert json.loads(await ext.recv())["kind"] == "heartbeat_ack"
                await ext.send(json.dumps({"kind":"tab_changed","tabId":401}))
                await asyncio.sleep(.05)
                status = await send_commands(SECRET,[{"action":"status"}],port)
                assert status[0]["result"]["connected"]
                assert status[0]["result"]["tab_id"] == 401
    asyncio.run(run())
