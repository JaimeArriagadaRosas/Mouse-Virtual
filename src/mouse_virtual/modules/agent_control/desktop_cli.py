"""Local desktop agent CLI. Explicit HWND target; no remote listener."""
import argparse,json,sys,time
from .commands import Command
from .desktop import DesktopExecutor
from .executor import AgentExecutor

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--hwnd",type=int,required=True)
    parser.add_argument("--action",required=True,choices=["find","fill","invoke","read","search"])
    parser.add_argument("--auto-id",default="")
    parser.add_argument("--name",default="")
    parser.add_argument("--control-type",default="Edit")
    parser.add_argument("--text",default="")
    parser.add_argument("--result-id",default="")
    args=parser.parse_args(argv)
    try:
        if not args.auto_id and not args.name:
            raise ValueError("Explicit control identifier required")
        executor=AgentExecutor(desktop=DesktopExecutor(args.hwnd))
        action={"find":"desktop.find_control","fill":"desktop.fill","invoke":"desktop.invoke","read":"desktop.read_control"}.get(args.action)
        if args.action=="search":
            if not args.result_id:raise ValueError("--result-id required for search")
            executor.execute(Command("desktop.fill",auto_id=args.auto_id,text=args.text))
            executor.execute(Command("desktop.invoke",name=args.name or "Buscar"))
            result=""
            for _ in range(30):
                result=executor.execute(Command("desktop.read_control",auto_id=args.result_id,control_type="Text"))["text"]
                if args.text in result:break
                time.sleep(.1)
            payload={"verified":args.text in result,"result":result}
        else:
            payload=executor.execute(Command(action,auto_id=args.auto_id,name=args.name,control_type=args.control_type,text=args.text))
        print(json.dumps({"ok":True,"result":payload},ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False),file=sys.stderr)
        return 1

if __name__=="__main__":raise SystemExit(main())
