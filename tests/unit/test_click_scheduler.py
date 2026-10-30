import pytest
from mouse_virtual.modules.clicker.scheduler import ClickBudget,ScheduleMetrics

def test_double_click_never_exceeds_odd_limit():
    budget=ClickBudget(50,5)
    sent=[]
    for _ in range(3):
        count=budget.allocate(2)
        sent.append(count)
        budget.record(count)
    assert sent==[2,2,1]
    assert budget.emitted==5
    assert budget.exhausted
    assert budget.allocate(2)==0

def test_unlimited_and_invalid_settings():
    budget=ClickBudget(100,None)
    for _ in range(1000):budget.record(budget.allocate(2))
    assert budget.emitted==2000 and not budget.exhausted
    with pytest.raises(ValueError):ClickBudget(1,100)
    with pytest.raises(ValueError):ClickBudget(50,0)
    with pytest.raises(ValueError):ClickBudget(50,-1)

def test_monotonic_schedule_metrics_with_fixed_clock():
    ticks=iter([0,50_500_000,100_800_000,150_900_000])
    measure=ScheduleMetrics(50,clock=lambda:next(ticks))
    measure.start()
    assert [round(measure.observe(),1) for _ in range(3)]==[0.5,0.8,0.9]
    assert measure.summary()["samples"]==3
    assert measure.summary()["drift_max_ms"]==0.9
