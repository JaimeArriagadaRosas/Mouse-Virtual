"""Validation for authorized local tab and group commands."""
from __future__ import annotations

import secrets
from pathlib import Path
from urllib.parse import urlparse

from mouse_virtual.modules.agent_control.browser_workflows import approved_upload_path

READ_ACTIONS = frozenset({"status", "inspect", "screenshot", "tab.list"})
WRITE_ACTIONS = frozenset({
    "move", "click", "type", "key", "navigate", "dom.click", "dom.fill", "file",
    "tab.select", "tab.select_id",
    "workspace.create", "workspace.open", "workspace.select", "workspace.close",
})
ACTIONS = READ_ACTIONS | WRITE_ACTIONS
KEYS = frozenset({
    "Enter", "Tab", "Escape", "Backspace", "ArrowDown", "ArrowUp",
    "ArrowLeft", "ArrowRight", "Delete",
})


def load_token(path: Path, *, create=False) -> str:
    path = Path(path).expanduser().resolve()
    if create and not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        # 256-bit secret, never printed by the server or put in source control.
        path.write_text(secrets.token_hex(32), encoding="ascii")
    token = path.read_text(encoding="ascii").strip()
    if len(token) != 64 or not all(c in "0123456789abcdef" for c in token):
        raise ValueError("Pairing file contains an invalid 256-bit token")
    return token


def validate_command(command, *, allow_writes=False, allow_hosts=(), file_roots=()):
    if not isinstance(command, dict) or set(command) - {"action", "x", "y",
          "text", "key", "url", "selector", "path", "index",
          "host", "urlPrefix", "tabId"}:
        raise ValueError("Unsupported command fields")
    action = command.get("action")
    if action not in ACTIONS:
        raise ValueError("Unsupported tab action")
    if action in WRITE_ACTIONS and not allow_writes:
        raise PermissionError("Use --allow-writes for commands modifying a page")
    expected = {"action"}
    if action in ("move", "click"):
        expected |= {"x", "y"}
        for axis in ("x", "y"):
            value = command.get(axis)
            if type(value) not in (int, float) or not 0 <= value <= 16384:
                raise ValueError("Invalid viewport coordinates")
    elif action == "tab.select":
        expected.add("host")
        host = command.get("host")
        if type(host) is not str or not host or host.lower() not in {
                item.lower() for item in allow_hosts}:
            raise PermissionError("Target tab host requires explicit authorization")
        if "urlPrefix" in command:
            expected.add("urlPrefix")
            prefix = command["urlPrefix"]
            parsed = urlparse(prefix) if type(prefix) is str else None
            if not parsed or parsed.scheme not in ("http", "https") or (
                    parsed.hostname or "").lower() != host.lower():
                raise ValueError("URL prefix must belong to the authorized host")
    elif action == "tab.select_id":
        expected |= {"tabId", "host"}
        tab_id = command.get("tabId")
        host = command.get("host")
        if type(tab_id) is not int or tab_id <= 0:
            raise ValueError("An explicit numeric tab ID is required")
        if type(host) is not str or host.lower() not in {
                item.lower() for item in allow_hosts}:
            raise PermissionError("Selection requires an explicitly authorized host")
    elif action in ("workspace.select", "workspace.close"):
        expected.add("tabId")
        if type(command.get("tabId")) is not int or command["tabId"] <= 0:
            raise ValueError("An explicit numeric workspace tab ID is required")
    elif action == "type":
        expected.add("text")
        if type(command.get("text")) is not str or not 1 <= len(command["text"]) <= 5000:
            raise ValueError("Text length must be 1..5000")
    elif action == "key":
        expected.add("key")
        if command.get("key") not in KEYS:
            raise ValueError("Key not allowed")
    elif action in ("navigate", "workspace.create", "workspace.open"):
        expected.add("url")
        url = command.get("url")
        if type(url) is not str or len(url) > 4096:
            raise ValueError("URL required")
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or parsed.username or parsed.password:
            raise ValueError("Only credential-free HTTP(S) URLs are permitted")
        if not allow_hosts or (parsed.hostname or "").lower() not in {
                x.lower() for x in allow_hosts}:
            raise PermissionError("Target host must be explicitly authorized")
    elif action in ("dom.click", "dom.fill", "file"):
        expected.add("selector")
        sel = command.get("selector")
        if type(sel) is not str or not 1 <= len(sel) <= 300:
            raise ValueError("A CSS selector of 1..300 characters is required")
        if action == "dom.fill":
            expected.add("text")
            if type(command.get("text")) is not str or len(command["text"]) > 5000:
                raise ValueError("Text length must be at most 5000")
        if action == "file":
            expected.add("path")
            # The extension cannot pick arbitrary local files.
            command = dict(command)
            command["path"] = str(approved_upload_path(command.get("path"), file_roots))
    if set(command) != expected:
        raise ValueError("Missing or unexpected fields")
    return command
