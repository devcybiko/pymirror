from datetime import datetime
import time

from pmtaskmgr.pmtask import PMTask
from pmlogger import _debug

from tables.time_table import TimeTable
from utils.utils import to_dict

class TimeTask(PMTask):
    def __init__(self, pmtm, config):
        super().__init__(pmtm, config)
        _debug(self.pmdb)
        self.pmdb.create_table(TimeTable)

    def exec(self):
        now = time.time()
        local = datetime.fromtimestamp(now)
        utc = datetime.utcfromtimestamp(now)
        local_date = local.strftime("%Y-%m-%d")
        local_time = local.strftime("%H:%M:%S")
        local_datetime = local.strftime("%Y-%m-%d %H:%M:%S")
        utc_date = utc.strftime("%Y-%m-%d")
        utc_time = utc.strftime("%H:%M:%S")
        utc_datetime = utc.strftime("%Y-%m-%d %H:%M:%S")
        timerec = TimeTable(
            id=0,
            epoch=now,
            local_date=local_date,
            local_time=local_time,
            local_datetime=local_datetime,
            utc_date=utc_date,
            utc_time=utc_time,
            utc_datetime=utc_datetime
        )
        _debug(to_dict(timerec))
        self.pmdb.upsert(timerec)
        record = self.pmdb.get(TimeTable, 0)
        _debug(to_dict(record))