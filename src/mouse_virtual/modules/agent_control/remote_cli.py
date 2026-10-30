"""CLI tool for remote orchestration with explicit per-request scope."""
import argparse,json,sys
from mouse_virtual.infrastructure.windows.handles import windows
from .runtime import execute_request

def main(argv=None):
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="operation",required=True)
    sub.add_parser("windows")
    inspect=sub.add_parser("inspect")
    inspect.add_argument("--hwnd",type=int,required=True)
    inspect.add_argument("--authorize-hwnd",type=int,required=True)
    run=sub.add_parser("run")
    run.add_argument("--hwnd",type=int,required=True)
    run.add_argument("--authorize-hwnd",type=int,required=True)
    run.add_argument("--plan",required=True,help="JSON file with steps, max 20")
    args=parser.parse_args(argv)
    try:
        if args.operation=="windows":
            payload={"ok":True,"windows":[{"hwnd":h,"title":t} for h,t in windows()]}
        else:
            req={"mode":args.operation,"hwnd":args.hwnd,"authorize_hwnd":args.authorize_hwnd}
            if args.operation=="run":
                from pathlib import Path
                plan=Path(args.plan)
                if plan.stat().st_size>20000:raise ValueError("Plan file too large")
                data=json.loads(plan.read_text(encoding="utf8"))
                req["steps"]=data["steps"]
            payload=execute_request(req)
        print(json.dumps(payload,ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"ok":False,"error_type":type(exc).__name__},ensure_ascii=False),file=sys.stderr)
        return 1
if __name__=="__main__":raise SystemExit(main())
