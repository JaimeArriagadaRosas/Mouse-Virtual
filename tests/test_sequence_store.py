from pathlib import Path
from tempfile import TemporaryDirectory
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sequence_store import SequenceStore
from plans import Step
def test_sequence_lifecycle():
    with TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder:
        s=SequenceStore(folder)
        a=s.create([Step('click',100,200)],infinite=True)
        assert a['name']=='Secuencia 1'
        assert s.get(a['id'])['infinite'] is True
        assert s.list()[0]['steps']==1
        a=s.update(a['id'],name='Compra de prueba',infinite=False,repeat=3)
        assert a['repeat']==3 and a['name']=='Compra de prueba'
        b=s.duplicate(a['id'])
        assert b['name']!='Compra de prueba'
        assert len(s.list())==2
        s.delete(a['id'])
        assert len(s.list())==1
def test_infinite_plan():
    from plans import Plan
    Plan([Step('click',1,2)],0).validate()
