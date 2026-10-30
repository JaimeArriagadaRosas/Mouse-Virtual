"""Click budgets and monotonic schedule accounting, independent of Qt or Win32."""
from dataclasses import dataclass
import time

MIN_INTERVAL_MS = 50

@dataclass
class ClickBudget:
    interval_ms: int
    limit: int | None
    emitted: int = 0

    def __post_init__(self):
        if not isinstance(self.interval_ms, int) or self.interval_ms < MIN_INTERVAL_MS:
            raise ValueError(f"Minimum interval: {MIN_INTERVAL_MS} ms")
        if self.limit is not None and (not isinstance(self.limit, int) or self.limit < 1):
            raise ValueError("Click limit must be positive")

    @property
    def remaining(self):
        return None if self.limit is None else max(0, self.limit-self.emitted)

    @property
    def exhausted(self):
        return self.remaining == 0

    def allocate(self, requested):
        if requested < 1:
            raise ValueError("Requested click count must be positive")
        if self.exhausted:
            return 0
        return requested if self.remaining is None else min(requested,self.remaining)

    def record(self, amount):
        if amount < 0:
            raise ValueError("Negative click count")
        if self.remaining is not None and amount > self.remaining:
            raise ValueError("Over budget")
        self.emitted += amount


class ScheduleMetrics:
    """Reports observed deadline drift; does not claim receiver delivery."""
    def __init__(self, interval_ms, clock=time.perf_counter_ns):
        if interval_ms < MIN_INTERVAL_MS:
            raise ValueError("Unsupported interval")
        self.period_ns=int(interval_ms*1_000_000)
        self.clock=clock
        self.start_ns=None
        self.samples_ns=[]

    def start(self):
        self.start_ns=self.clock()
        self.samples_ns.clear()

    def observe(self):
        if self.start_ns is None:
            raise RuntimeError("Scheduler was not started")
        index=len(self.samples_ns)+1
        actual=self.clock()
        error=actual-(self.start_ns+self.period_ns*index)
        self.samples_ns.append(error)
        return error/1_000_000

    def summary(self):
        ordered=sorted(self.samples_ns)
        count=len(ordered)
        if not count:return {"samples":0}
        def percentile(p):return ordered[int((count-1)*p)]/1_000_000
        return {"samples":count,"drift_p50_ms":round(percentile(.5),3),
                "drift_p95_ms":round(percentile(.95),3),
                "drift_p99_ms":round(percentile(.99),3),
                "drift_max_ms":round(ordered[-1]/1_000_000,3)}
