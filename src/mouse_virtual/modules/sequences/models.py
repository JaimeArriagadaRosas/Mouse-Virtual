"""Planes originales de automatizacion, sin reutilizar codigo de referencia."""
from dataclasses import dataclass,asdict
from pathlib import Path
import json

ALLOWED={"click","wait"}

@dataclass(frozen=True)
class Step:
    action:str
    x:int=0
    y:int=0
    button:str="left"
    delay_ms:int=0

    def validate(self):
        if self.action not in ALLOWED:raise ValueError("Accion no compatible")
        if self.button not in ("left","right"):raise ValueError("Boton invalido")
        if self.delay_ms<0 or self.delay_ms>3600000:raise ValueError("Pausa fuera de rango")
        if self.x<0 or self.y<0 or self.x>32767 or self.y>32767:raise ValueError("Coordenadas fuera de rango")

@dataclass
class Plan:
    steps:list[Step]
    repeat:int=1
    def validate(self):
        if not self.steps or len(self.steps)>500:raise ValueError("Pasos invalidos")
        if not 0<=self.repeat<=10000:raise ValueError("Repeticiones invalidas")  # 0 = infinito
        for step in self.steps:step.validate()
    def save(self,path):
        self.validate()
        Path(path).write_text(json.dumps({"repeat":self.repeat,"steps":[asdict(s) for s in self.steps]},indent=2),encoding="utf8")
    @classmethod
    def load(cls,path):
        raw=json.loads(Path(path).read_text(encoding="utf8"))
        plan=cls([Step(**item) for item in raw["steps"]],int(raw["repeat"]))
        plan.validate()
        return plan
