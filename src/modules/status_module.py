from datetime import datetime
import os
import sys
from pymirror.pmmodule import PMModule
from pymirror.pmtimer import PMTimer
from pymirror.utils.utils import pprint, strftime_by_example, glyphs, to_secs

class StatusModule(PMModule):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._status = config.status
        self.interval_secs = to_secs(self._status.interval_time)
        self.timer = PMTimer(self._status.interval_time)
        self._status.time_format = strftime_by_example(self._status.time_format)
        self.pmstatus = self.pm.get_status()
        pprint(self.pmstatus)

    def render(self, force: bool = False) -> bool:
        pmstatus = self.pmstatus
        taskmgr = self.pmstatus.taskmgr
        if taskmgr:
            tm = f"{int(taskmgr.pstat.delta.total_cpu * 1000 / self.interval_secs)}{glyphs.up} "
        else:
            tm = f"{0}{glyphs.down} "

        self.bitmap.clear()
        self.bitmap.text_box((0, 0, self.bitmap.width-1, self.bitmap.height-1), 
        	f"DB:{glyphs.yes if pmstatus.debug else glyphs.no} "\
            f"RM:{glyphs.yes if pmstatus.remote_display else glyphs.no} "
            f"TM:{tm} "
            f"  {pmstatus.start_time.strftime(self._status.time_format)}", 
        	valign=self._status.valign, halign=self._status.halign)
        return True

    def exec(self):
        if self.timer.is_timedout():
            self.timer.reset()
            self.pmstatus = self.pm.get_status()
            pprint(self.pmstatus.taskmgr)
            return True
        return False

    def onEvent(self, event):
        pass			

