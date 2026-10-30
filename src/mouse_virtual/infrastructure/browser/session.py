"""Playwright adapter using a dedicated Chromium context."""
class BrowserSession:
    def __init__(self,headless=True,allowed_hosts=None):
        self.headless=headless
        self.allowed_hosts=set(allowed_hosts or {"localhost","127.0.0.1"})
        self.manager=self.browser=self.context=self.page=None
    def __enter__(self):
        try:from playwright.sync_api import sync_playwright
        except ImportError as exc:raise RuntimeError("Install pip package playwright and its Chromium browser") from exc
        self.manager=sync_playwright().start()
        try:
            self.browser=self.manager.chromium.launch(headless=self.headless)
            self.context=self.browser.new_context()
            self.context.route('**/*',self._route)
            self.page=self.context.new_page()
        except:
            self.manager.stop()
            raise
        return self
    def __exit__(self,*args):
        if self.browser:self.browser.close()
        if self.manager:self.manager.stop()
    def _route(self,route):
        from urllib.parse import urlparse
        u=urlparse(route.request.url)
        if u.scheme in ('http','https') and (u.hostname or '').lower() in self.allowed_hosts:
            route.continue_()
        else:
            route.abort()
    def open(self,url):
        from urllib.parse import urlparse
        host=(urlparse(url).hostname or "").lower()
        if host not in self.allowed_hosts:raise PermissionError("Host not allowlisted")
        self.page.goto(url,wait_until="domcontentloaded",timeout=15000)
        return {"url":self.page.url,"title":self.page.title()}
    def locate(self,role="",name=""):
        if role and name:return self.page.get_by_role(role,name=name)
        if name:return self.page.get_by_label(name).or_(self.page.get_by_placeholder(name)).first
        raise ValueError("Role/name required")
    def fill(self,text,role="",name=""):
        self.locate(role,name).fill(text)
        return {"filled":True,"length":len(text)}
    def click(self,role="",name=""):
        self.locate(role,name).click()
        return {"clicked":True}
    def read_page(self):
        return {"url":self.page.url,"title":self.page.title(),"text":self.page.locator("body").inner_text()[:5000]}
