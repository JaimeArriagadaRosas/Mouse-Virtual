"""Persistent named sequences stored independently from the GUI and recordings."""
from __future__ import annotations
import json, os, uuid, tempfile
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict
from mouse_virtual.modules.sequences.models import Plan, Step

DEFAULT_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "MouseVirtual" / "sequences"

class SequenceStore:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else DEFAULT_DIR
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, seq_id):
        if not isinstance(seq_id,str) or len(seq_id)!=32 or any(ch not in "0123456789abcdef" for ch in seq_id):
            raise ValueError("Identificador de secuencia inválido")
        return self.root / f"{seq_id}.json"

    def list(self):
        items=[]
        for p in self.root.glob("*.json"):
            try:
                item=json.loads(p.read_text(encoding="utf-8"))
                if item.get("id")==p.stem:
                    items.append({"id":item["id"],"name":item["name"],"updated_at":item.get("updated_at",""),"steps":len(item.get("steps",[]))})
            except (OSError,ValueError,KeyError,TypeError):
                continue
        return sorted(items,key=lambda x:(x["name"].casefold(),x["id"]))

    def get(self,seq_id):
        data=json.loads(self._path(seq_id).read_text(encoding="utf-8"))
        if data.get("id")!=seq_id:raise ValueError("ID inconsistente")
        steps=[Step(**x) for x in data["steps"]]
        Plan(steps,0 if data.get("infinite",True) else data.get("repeat",1)).validate()
        return data

    def _write(self, data):
        target=self._path(data["id"])
        temp=target.with_suffix(".tmp")
        try:
            temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
            os.replace(temp,target)
        finally:
            if temp.exists():temp.unlink()
        return data

    def next_name(self):
        names={item["name"].casefold() for item in self.list()}
        i=1
        while f"secuencia {i}" in names:i+=1
        return f"Secuencia {i}"

    def create(self,steps,name=None,infinite=True,repeat=1,target_title="",geometry=None):
        steps=list(steps)
        Plan(steps,0 if infinite else repeat).validate()
        name=(name or self.next_name()).strip()
        if not name or len(name)>100:raise ValueError("Nombre inválido")
        if any(item["name"].casefold()==name.casefold() for item in self.list()):
            raise ValueError("Ya existe una secuencia con ese nombre")
        now=datetime.now(timezone.utc).isoformat()
        return self._write({"version":1,"id":uuid.uuid4().hex,"name":name,
            "steps":[asdict(s) for s in steps],"infinite":bool(infinite),"repeat":int(repeat),
            "target_title":target_title,"geometry":geometry,"created_at":now,"updated_at":now})

    def update(self,seq_id,*,name=None,steps=None,infinite=None,repeat=None):
        data=self.get(seq_id)
        if name is not None:
            name=name.strip()
            if not name or len(name)>100:raise ValueError("Nombre inválido")
            if any(x["id"]!=seq_id and x["name"].casefold()==name.casefold() for x in self.list()):
                raise ValueError("Ya existe otra secuencia con ese nombre")
            data["name"]=name
        if steps is not None:
            data["steps"]=[asdict(s) for s in steps]
        if infinite is not None:data["infinite"]=bool(infinite)
        if repeat is not None:data["repeat"]=int(repeat)
        Plan([Step(**s) for s in data["steps"]],0 if data["infinite"] else data["repeat"]).validate()
        data["updated_at"]=datetime.now(timezone.utc).isoformat()
        return self._write(data)

    def duplicate(self,seq_id):
        data=self.get(seq_id)
        base=data["name"]+" copia"
        name=base
        suffix=2
        names={x["name"].casefold() for x in self.list()}
        while name.casefold() in names:
            name=f"{base} {suffix}";suffix+=1
        return self.create([Step(**x) for x in data["steps"]],name,data["infinite"],data["repeat"],data.get("target_title",""),data.get("geometry"))

    def delete(self,seq_id):
        self._path(seq_id).unlink()
