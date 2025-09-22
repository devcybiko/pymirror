from datetime import datetime
import os
import sys
from pymirror.pmmodule import PMModule
from pymirror.pmtimer import PMTimer
from pymirror.utils import strftime_by_example

class StatusModule(PMModule):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._status = config.status
        self.timer = PMTimer(self._status.interval_time)
        self._status.time_format = strftime_by_example(self._status.time_format)

    def render(self, force: bool = False) -> bool:
        pmstatus = self.pm.get_status()
        yes = '\u25CF'
        no = '\u25CB'
        self.bitmap.clear()
        self.bitmap.text_box((0, 0, self.bitmap.width-1, self.bitmap.height-1), 
        	f"DEBUG: {yes if pmstatus.debug else no} REMOTE: {yes if pmstatus.remote_display else no} STARTUP: {pmstatus.start_time.strftime(self._status.time_format)}", 
        	valign=self._status.valign, halign=self._status.halign)
        return True

    def exec(self):
        return True

    def onEvent(self, event):
        pass			

