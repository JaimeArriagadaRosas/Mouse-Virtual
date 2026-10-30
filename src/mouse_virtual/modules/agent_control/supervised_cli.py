"""Run the CLI in a disposable process with a hard execution timeout."""
import argparse,json,subprocess,sys

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--timeout",type=float,default=12)
    parser.add_argument("command",nargs=argparse.REMAINDER)
    args=parser.parse_args(argv)
    if not 1<=args.timeout<=60:
        parser.error("timeout must be 1..60 seconds")
    if not args.command or args.command[0] not in ("windows","inspect","run"):
        parser.error("Provide windows, inspect or run")
    cmd=[sys.executable,"-m","mouse_virtual.modules.agent_control.remote_cli",*args.command]
    try:
        completed=subprocess.run(cmd,capture_output=True,text=True,timeout=args.timeout)
        if completed.returncode==0:
            print(completed.stdout.strip())
            return 0
        try:
            result=json.loads(completed.stderr.strip())
            if not isinstance(result,dict):raise ValueError()
        except (ValueError,TypeError):
            result={"ok":False,"error_type":"InvalidArguments"}
        print(json.dumps(result,ensure_ascii=False))
        return completed.returncode
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok":False,"error_type":"TimeoutExpired","timeout_seconds":args.timeout}))
        return 124
if __name__=="__main__":
    raise SystemExit(main())
