from mouse_virtual.modules.sequences.models import Plan,Step
def test_middle_button_in_serialized_plan(tmp_path):
    p=Plan([Step("click",20,30,"middle",1)],1)
    f=tmp_path/"middle.json"
    p.save(f)
    assert Plan.load(f).steps[0].button=="middle"
