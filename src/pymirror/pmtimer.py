import time
from pymirror.pmlogger import _debug, trace
from pymirror.utils import to_ms

class PMTimer:
    def __init__(self, delay_ms=0, first_timeout_ms=1):
        self.future_time = 0
        self.delay_ms = to_ms(delay_ms)
        self.set_future_time(first_timeout_ms)

    def reset(self, delay_ms=None):
        _debug(f"PMTimer.reset()")
        if delay_ms is not None:
            self.set_future_time(delay_ms)
        else:
            self.set_future_time(self.delay_ms)

    def set_future_time(self, delay_ms):
        _debug(f"PMTimer.set_future_time({delay_ms})")
        now = time.time()
        self.future_time = now + delay_ms / 1000

    def set_timeout(self, delay_ms, first_timeout_ms=1):
        _debug(f"PMTimer.set_timeout({delay_ms}, {first_timeout_ms})")
        if not delay_ms or delay_ms < 0:
            self.future_time = 0 ## disable timer
        else:
            self.delay_ms = delay_ms
            self.set_future_time(first_timeout_ms)

    def is_timedout(self, reset_ms: int = None):
        if not self.future_time:
            return False # disabled timer always returns False
        now = time.time()
        if now < self.future_time:
            return False ## we're not timed out yet
        else:
            if reset_ms != None:
                self.set_timeout(reset_ms) ## reset timer (0=disable, 1=1ms retry, None = perpetuate)
            return True
