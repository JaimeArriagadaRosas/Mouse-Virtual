"""Run an approved browser plan in a separate Playwright Chromium session.

This program does not access the user's visible browser, global mouse, keyboard,
session cookies or profiles unless a dedicated profile directory is supplied.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .browser_workflows import MAX_BYTES, execute_plan, plan_digest, validate_plan


def _repo_root():
    return Path(__file__).resolve().parents[4]


def _ensure_untracked_location(target, label):
    if target is None:
        return
    candidate = Path(target).resolve()
    if candidate.is_relative_to(_repo_root()):
        raise PermissionError(f"{label} must be outside the source repository")


def main(argv=None):
    p = argparse.ArgumentParser(description="Isolated, scoped Chromium workflow executor")
    p.add_argument("--plan", required=True, help="Local JSON plan; max 64 KiB")
    p.add_argument("--allow-host", required=True, action="append", dest="hosts")
    p.add_argument("--profile-dir", help="Dedicated Chromium profile, OUTSIDE this repository")
    p.add_argument("--artifacts-dir", help="Optional screenshots directory, OUTSIDE this repository")
    p.add_argument("--allow-file-root", action="append", dest="file_roots", default=[],
                   help="Explicit root that may supply video files for upload_file")
    p.add_argument("--report", help="Write JSON result to a location OUTSIDE this repository")
    p.add_argument("--headful", action="store_true", help="Show isolated browser window")
    p.add_argument("--allow-writes", action="store_true", help="Enable fill, click and select")
    p.add_argument("--dry-run", action="store_true", help="Validate without opening browser")
    p.add_argument("--timeout-ms", type=int, default=12000)
    args = p.parse_args(argv)
    try:
        planfile = Path(args.plan).resolve()
        if not planfile.is_file() or planfile.stat().st_size > MAX_BYTES:
            raise ValueError("Plan missing or larger than 64 KiB")
        plan = json.loads(planfile.read_text(encoding="utf-8"))
        allowed_hosts = {name.strip().lower() for name in args.hosts}
        if not 1000 <= args.timeout_ms <= 60000:
            raise ValueError("Per-action timeout must be between 1000 and 60000 ms")
        _ensure_untracked_location(args.profile_dir, "Browser profile")
        _ensure_untracked_location(args.artifacts_dir, "Artifacts")
        _ensure_untracked_location(args.report, "Report")
        validated = validate_plan(plan, allowed_hosts=allowed_hosts,
                                  allow_writes=(args.dry_run or args.allow_writes),
                                  allowed_file_roots=args.file_roots)
        if args.dry_run:
            result = {"ok": True, "dry_run": True, "step_count": len(validated),
                      "actions": [step["action"] for step in validated],
                      "plan_sha256": plan_digest(plan),
                      "writes_requested": any(s["action"] in ("fill", "click", "select", "press",
                                                               "upload_file") for s in validated)}
        else:
            result = execute_plan(plan, allowed_hosts=allowed_hosts,
                                  allow_writes=args.allow_writes,
                                  allowed_file_roots=args.file_roots,
                                  headless=not args.headful,
                                  profile_dir=args.profile_dir,
                                  artifacts_dir=args.artifacts_dir,
                                  timeout_ms=args.timeout_ms)
        if args.report:
            out = Path(args.report).resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        # The state of an interrupted action may be uncertain. Never retry.
        payload = {"ok": False, "status": "uncertain_no_auto_retry",
                   "error_type": type(exc).__name__, "error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        if args.report:
            try:
                out = Path(args.report).resolve()
                _ensure_untracked_location(out, "Report")
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except OSError:
                pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
