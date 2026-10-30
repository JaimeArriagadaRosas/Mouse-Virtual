import argparse,json,sys
from .commands import Command
from .executor import AgentExecutor
from mouse_virtual.infrastructure.browser.session import BrowserSession
def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--url",required=True)
    p.add_argument("--query",required=True)
    p.add_argument("--allowed-host",default="localhost")
    p.add_argument("--headful",action="store_true")
    a=p.parse_args(argv)
    try:
        with BrowserSession(headless=not a.headful,allowed_hosts={a.allowed_host}) as browser:
            agent=AgentExecutor(browser)
            agent.execute(Command("browser.open",url=a.url))
            result=agent.execute(Command("browser.search",query=a.query))
        print(json.dumps({"ok":True,"result":result},ensure_ascii=False));return 0
    except Exception as exc:
        print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
