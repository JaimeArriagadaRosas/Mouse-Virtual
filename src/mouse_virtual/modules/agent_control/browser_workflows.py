"""Strict, transport-independent browser workflow runner.

The package never references any external account, website, channel or project.
Only an explicit host allowlist can authorize navigation. There are no OS-wide
mouse/keyboard calls or raw JavaScript execution.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from mouse_virtual.infrastructure.browser.session import BrowserSession

MAX_STEPS = 40
MAX_BYTES = 65536
WRITES = frozenset(("fill", "click", "select", "press"))
ACTIONS = frozenset(("open", "fill", "click", "select", "press",
                     "assert_text", "assert_url", "read_text", "screenshot"))
SAFE_SCREENSHOT_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$")
MAX_FIELD_LENGTH = 4000


def approved_url(url: str, allowed_hosts: set[str]) -> str:
    if type(url) is not str or len(url) > 4096:
        raise ValueError("URL must be a string under 4096 characters")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or (parsed.hostname or "").lower() not in allowed_hosts:
        raise PermissionError("URL host not authorized")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in URLs are forbidden")
    return url


def _text(value, field, limit=MAX_FIELD_LENGTH):
    if type(value) is not str or not value or len(value) > limit:
        raise ValueError(f"{field} requires a nonempty string of at most {limit} chars")
    return value


def validate_plan(plan, *, allowed_hosts: set[str], allow_writes=False):
    if not isinstance(plan, dict) or set(plan) - {"version", "steps", "name"}:
        raise ValueError("Plan must be an object with version, name and steps")
    if plan.get("version") != 1:
        raise ValueError("Unsupported plan version")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not (1 <= len(steps) <= MAX_STEPS):
        raise ValueError(f"Plan must contain 1 to {MAX_STEPS} steps")
    if "name" in plan:
        _text(plan["name"], "name", 120)
    if not allowed_hosts or any(not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", h) for h in allowed_hosts):
        raise ValueError("An explicit host allowlist is required")
    seen_open = False
    validated = []
    for i, step in enumerate(steps):
        if type(step) is not dict:
            raise ValueError(f"Invalid step {i}")
        act = step.get("action")
        if act not in ACTIONS:
            raise ValueError(f"Unsupported action at step {i}")
        if act in WRITES and not allow_writes:
            raise PermissionError("Mutating steps require explicit --allow-writes")
        allowed_fields = {"action"}
        if act == "open":
            allowed_fields.add("url")
            approved_url(step.get("url"), allowed_hosts)
            seen_open = True
        else:
            if not seen_open:
                raise ValueError("The first browser step must be open")
            if act in ("fill", "click", "select", "press", "assert_text", "read_text"):
                allowed_fields.update(("role", "name"))
                _text(step.get("role"), "role", 48)
                _text(step.get("name"), "name", 200)
            if act == "fill":
                allowed_fields.add("value")
                _text(step.get("value"), "value")
            if act == "select":
                allowed_fields.add("value")
                _text(step.get("value"), "value", 200)
            if act == "press":
                allowed_fields.add("key")
                if step.get("key") not in ("Enter", "Tab", "Escape", "ArrowDown", "ArrowUp"):
                    raise ValueError("Key not allowed")
            if act == "assert_text":
                allowed_fields.add("contains")
                _text(step.get("contains"), "contains", 1000)
            if act == "assert_url":
                allowed_fields.add("contains")
                _text(step.get("contains"), "contains", 1000)
            if act == "screenshot":
                allowed_fields.add("name")
                if not SAFE_SCREENSHOT_NAME.fullmatch(_text(step.get("name"), "screenshot name", 80)):
                    raise ValueError("Invalid screenshot filename")
        if set(step) - allowed_fields:
            raise ValueError(f"Unsupported fields in step {i}")
        validated.append(step)
    if not seen_open:
        raise ValueError("Plan must open at least one page")
    return validated


def plan_digest(plan):
    return hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf8")).hexdigest()


def execute_plan(plan, *, allowed_hosts: set[str], allow_writes=False,
                 headless=True, profile_dir=None, artifacts_dir=None,
                 session_factory=BrowserSession, timeout_ms=12000):
    steps = validate_plan(plan, allowed_hosts=allowed_hosts, allow_writes=allow_writes)
    artifacts = Path(artifacts_dir).resolve() if artifacts_dir else None
    if any(step["action"] == "screenshot" for step in steps) and artifacts is None:
        raise ValueError("An explicit artifacts directory is required for screenshots")
    if artifacts is not None:
        artifacts.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    result = {"ok": False, "name": plan.get("name", "unnamed"),
              "plan_sha256": plan_digest(plan), "completed": 0, "steps": []}
    with session_factory(headless=headless, allowed_hosts=allowed_hosts,
                         profile_dir=profile_dir, timeout_ms=timeout_ms) as session:
        page = None
        for index, step in enumerate(steps):
            action = step["action"]
            if action == "open":
                entry = session.open(step["url"])
                detail = {"title": entry["title"], "url": entry["url"]}
                page = session.page
            elif action == "assert_url":
                if step["contains"] not in page.url:
                    raise AssertionError(f"URL assertion failed at step {index}")
                detail = {"verified": True}
            elif action == "screenshot":
                path = artifacts / (step["name"] + ".png")
                page.screenshot(path=str(path), animations="disabled", timeout=timeout_ms)
                detail = {"captured": True, "filename": path.name}
            else:
                target = page.get_by_role(step["role"], name=step["name"], exact=True).first
                if action == "fill":
                    target.fill(step["value"], timeout=timeout_ms)
                    detail = {"filled": True, "length": len(step["value"])}
                elif action == "click":
                    target.click(timeout=timeout_ms)
                    detail = {"clicked": True}
                elif action == "select":
                    target.select_option(label=step["value"], timeout=timeout_ms)
                    detail = {"selected": True}
                elif action == "press":
                    target.press(step["key"], timeout=timeout_ms)
                    detail = {"pressed": True}
                elif action == "assert_text":
                    from playwright.sync_api import expect
                    expect(target).to_contain_text(step["contains"], timeout=timeout_ms)
                    detail = {"verified": True}
                elif action == "read_text":
                    value = target.inner_text(timeout=timeout_ms)
                    detail = {"text": value[:2000], "truncated": len(value) > 2000}
                else:
                    raise AssertionError("Unexpected validated action")
                # After each action, any redirected page must remain on the allowlist.
                approved_url(page.url, allowed_hosts)
            result["steps"].append({"index": index, "action": action, "result": detail})
            result["completed"] += 1
    result["ok"] = True
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return result
