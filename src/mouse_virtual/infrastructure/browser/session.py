"""Playwright browser session with an independent Chromium context.

No global input, shared desktop mouse or attached user browser.
A persistent profile is optional and must be explicitly supplied by the caller.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

class BrowserSession:
    def __init__(self, headless=True, allowed_hosts=None, profile_dir=None, timeout_ms=15000):
        self.headless = headless
        self.allowed_hosts = {x.lower() for x in (allowed_hosts or {"localhost", "127.0.0.1"})}
        self.profile_dir = Path(profile_dir).resolve() if profile_dir else None
        self.timeout_ms = int(timeout_ms)
        self.manager = self.browser = self.context = self.page = None

    def __enter__(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Install playwright and its Chromium browser") from exc
        self.manager = sync_playwright().start()
        try:
            if self.profile_dir is not None:
                self.profile_dir.mkdir(parents=True, exist_ok=True)
                self.context = self.manager.chromium.launch_persistent_context(
                    user_data_dir=str(self.profile_dir), headless=self.headless,
                    accept_downloads=False,
                )
                self.browser = self.context.browser
            else:
                self.browser = self.manager.chromium.launch(headless=self.headless)
                self.context = self.browser.new_context(accept_downloads=False)
            self.context.route("**/*", self._route)
            self.context.set_default_timeout(self.timeout_ms)
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *args):
        try:
            if self.context:
                self.context.close()
            elif self.browser:
                self.browser.close()
        finally:
            if self.manager:
                self.manager.stop()
            self.manager = self.browser = self.context = self.page = None

    def _check_url(self, url):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or (parsed.hostname or "").lower() not in self.allowed_hosts:
            raise PermissionError("Target URL is outside the approved hosts")
        return url

    def _route(self, route):
        try:
            self._check_url(route.request.url)
        except PermissionError:
            route.abort()
        else:
            route.continue_()

    def open(self, url):
        self._check_url(url)
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        self._check_url(self.page.url)
        return {"url": self.page.url, "title": self.page.title()}

    def locate(self, role="", name=""):
        if role and name:
            return self.page.get_by_role(role, name=name).first
        if name:
            return self.page.get_by_label(name).or_(self.page.get_by_placeholder(name)).first
        raise ValueError("Role or label/name is required")

    def fill(self, text, role="", name=""):
        self.locate(role, name).fill(text)
        return {"filled": True, "length": len(text)}

    def click(self, role="", name=""):
        self.locate(role, name).click()
        return {"clicked": True}

    def read_page(self):
        return {"url": self.page.url, "title": self.page.title(),
                "text": self.page.locator("body").inner_text()[:5000]}
