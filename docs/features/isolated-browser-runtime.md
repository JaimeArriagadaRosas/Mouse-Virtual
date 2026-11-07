# Isolated browser automation runtime

This experimental branch adds a general-purpose, composable browser workflow runner. It is not a desktop mouse emulator. Chromium runs in a separate Playwright-managed browser process with `headless` mode enabled by default, so normal actions do not take control of the user's system cursor, focus, or keyboard.

## Security and privacy boundaries

- Only an explicit host allowlist can authorize network navigation and resource requests.
- Plans use a small JSON action vocabulary; arbitrary JavaScript, shell commands, file reading and unapproved URLs are not supported.
- Form mutations require the explicit `--allow-writes` flag, while `--dry-run` validates without browser launch.
- Profiles, screenshots, and machine-readable reports must be stored outside the Git repository. No profile is shared with a user's personal browser.
- The executable does not read browser cookies from other running sessions or collect credentials.
- Interrupted or failed write actions are uncertain; the runner does not retry them.
- No website-specific data, organization identities, accounts, tokens, videos, URLs or publication schedules belong to this branch.

## Example dry run

Create a local `plan.json` outside the repository:

```json
{
  "version": 1,
  "name": "Local form check",
  "steps": [
    {"action": "open", "url": "http://127.0.0.1:8080"},
    {"action": "fill", "role": "textbox", "name": "Question", "value": "example"},
    {"action": "click", "role": "button", "name": "Search"},
    {"action": "assert_text", "role": "status", "name": "Outcome", "contains": "Found"}
  ]
}
```

```powershell
$env:PYTHONPATH = ".\src"
python -m mouse_virtual.modules.agent_control.browser_workflow_cli `
  --plan "D:\MyPrivatePlans\plan.json" --allow-host 127.0.0.1 --dry-run
```

To run a trusted plan, omit `--dry-run`, provide `--allow-writes` and optionally set `--artifacts-dir` to a directory outside the repository. Headless operation is the default; `--headful` intentionally launches a visible window and may disrupt desktop usage.

## Scope and known limitations

- Headless Chromium does not inherit authentication from an unrelated open Chrome tab. Authenticate a dedicated browser profile separately before reusing it.
- Some sites block automation or require interactive verification; no CAPTCHA bypass is implemented.
- The command is bounded by step count and per-action timeouts but has no resumable job queue yet.
- The desktop Win32/UIA adapter is a separate fallback; it does not guarantee independence from system focus.
- This is an experiment on a feature branch, not a promise of merge into the product branch.

## Tests

The suite covers plan validation, host restrictions, permissions, screenshots, CLI dry runs, independent Chromium operation and the pre-existing mouse/keyboard features.

```powershell
$env:PYTHONPATH = ".\src"
python -m pytest -q tests --basetemp=.pytest_temp\full --disable-warnings
```
