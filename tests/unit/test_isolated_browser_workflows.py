"""Generic workflow validation and independent-execution tests."""
import pytest
from mouse_virtual.modules.agent_control.browser_workflows import (
    MAX_STEPS, approved_url, execute_plan, validate_plan,
)

LOCAL = {"127.0.0.1", "localhost"}


def plan(*steps):
    return {"version": 1, "name": "Local fixture", "steps": list(steps)}


def open_step():
    return {"action": "open", "url": "http://127.0.0.1:8080/"}


def test_only_explicit_hosts_are_authorized():
    assert approved_url("http://127.0.0.1:80/x", LOCAL)
    with pytest.raises(PermissionError):
        approved_url("https://example.org", LOCAL)
    with pytest.raises(ValueError):
        approved_url("https://admin:pass@localhost", LOCAL)
    with pytest.raises(PermissionError):
        approved_url("file:///etc/passwd", LOCAL)


def test_mutations_require_explicit_permission():
    payload = plan(open_step(), {"action": "fill", "role": "textbox", "name": "Query", "value": "testing"})
    with pytest.raises(PermissionError):
        validate_plan(payload, allowed_hosts=LOCAL)
    assert len(validate_plan(payload, allowed_hosts=LOCAL, allow_writes=True)) == 2


def test_rejects_unsupported_steps_and_fields():
    with pytest.raises(ValueError):
        validate_plan(plan({"action": "click", "role": "button", "name": "Go"}),
                      allowed_hosts=LOCAL, allow_writes=True)
    with pytest.raises(ValueError):
        validate_plan(plan(open_step(), {"action": "execute_js", "value": "alert(1)"}),
                      allowed_hosts=LOCAL, allow_writes=True)
    with pytest.raises(ValueError):
        validate_plan(plan({"action": "open", "url": "http://127.0.0.1", "secrets": "x"}),
                      allowed_hosts=LOCAL)
    with pytest.raises(ValueError):
        validate_plan(plan(*(open_step() for _ in range(MAX_STEPS + 1))),
                      allowed_hosts=LOCAL)


def test_screenshot_cannot_escape_artifacts_folder():
    with pytest.raises(ValueError):
        validate_plan(plan(open_step(), {"action": "screenshot", "name": "../cookie"}),
                      allowed_hosts=LOCAL)
    with pytest.raises(ValueError):
        validate_plan(plan(open_step(), {"action": "press", "role": "textbox",
                                        "name": "Query", "key": "Control+L"}),
                      allowed_hosts=LOCAL, allow_writes=True)


class FakeLocator:
    @property
    def first(self):
        return self
    def fill(self, value, timeout=None):
        assert value == "text"
    def click(self, timeout=None):
        pass
    def inner_text(self, timeout=None):
        return "Results: text"


class FakePage:
    url = "http://127.0.0.1:8080/"
    def get_by_role(self, role, name, exact):
        assert exact
        return FakeLocator()


class FakeSession:
    def __init__(self, **kwargs):
        assert kwargs["allowed_hosts"] == LOCAL
        self.page = FakePage()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def open(self, url):
        return {"url": url, "title": "Fixture"}


def test_generic_engine_runs_without_global_input():
    request = plan(
        open_step(),
        {"action": "fill", "role": "textbox", "name": "Query", "value": "text"},
        {"action": "click", "role": "button", "name": "Go"},
        {"action": "read_text", "role": "status", "name": "Result"},
        {"action": "assert_url", "contains": "127.0.0.1"},
    )
    r = execute_plan(request, allowed_hosts=LOCAL, allow_writes=True,
                     session_factory=FakeSession)
    assert r["ok"] is True
    assert r["completed"] == 5
    assert r["steps"][1]["result"] == {"filled": True, "length": 4}
    assert r["steps"][3]["result"]["text"] == "Results: text"


def test_media_upload_requires_explicit_file_root_and_writes(tmp_path):
    folder = tmp_path / "approved"
    folder.mkdir()
    video = folder / "sample.mp4"
    video.write_bytes(b"video-fixture" * 100)
    payload = plan(open_step(), {"action": "upload_file", "path": str(video)})
    with pytest.raises(PermissionError):
        validate_plan(payload, allowed_hosts=LOCAL, allow_writes=False,
                      allowed_file_roots=[folder])
    with pytest.raises(PermissionError):
        validate_plan(payload, allowed_hosts=LOCAL, allow_writes=True)
    assert len(validate_plan(payload, allowed_hosts=LOCAL, allow_writes=True,
                             allowed_file_roots=[folder])) == 2


def test_media_upload_rejects_secrets_and_path_traversal(tmp_path):
    approved = tmp_path / "allowed"
    blocked = tmp_path / "blocked"
    approved.mkdir()
    blocked.mkdir()
    secret = blocked / "private.mp4"
    secret.write_bytes(b"fake")
    payload = plan(open_step(), {"action": "upload_file", "path": str(secret)})
    with pytest.raises(PermissionError):
        validate_plan(payload, allowed_hosts=LOCAL, allow_writes=True,
                      allowed_file_roots=[approved])
    invalid = approved / "secrets.json"
    invalid.write_text("{}")
    with pytest.raises(ValueError):
        validate_plan(plan(open_step(), {"action": "upload_file", "path": str(invalid)}),
                      allowed_hosts=LOCAL, allow_writes=True,
                      allowed_file_roots=[approved])


def test_file_input_index_is_bounded(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"abc")
    payload = plan(open_step(), {"action": "upload_file", "path": str(video), "index": 6})
    with pytest.raises(ValueError):
        validate_plan(payload, allowed_hosts=LOCAL, allow_writes=True,
                      allowed_file_roots=[tmp_path])
