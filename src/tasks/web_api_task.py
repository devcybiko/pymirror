from datetime import datetime
import json
import time
from sqlalchemy import Column, DateTime, Integer, String, and_
from pmdb.pmdb import Base
from sqlalchemy.orm import declarative_base

from pmtaskmgr.pmtask import PMTask
from pymirror.utils.utils import json_dumps, json_loads, to_secs
from pymirror.pmlogger import _debug, _error

import requests

Base = declarative_base()

class WebApiTable(Base):
    __tablename__ = 'webapi'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    last_time = Column(DateTime)
    last_rc = Column(Integer)
    rate_limit_secs = Column(Integer)
    retry_after_secs = Column(Integer)
    result_text = Column(String)
    params = Column(String)

class WebApiTask(PMTask):
    def __init__(self, pmtm, config):
        super().__init__(pmtm, config)
        self.pmdb.create_table(WebApiTable, checkfirst=True, force=False)
        record = self.pmdb.get_where(WebApiTable, WebApiTable.name == self.name)
        print(33, self._task)
        if not record:
            record = WebApiTable(
                name=self.name,
                url = self._task.url,
                last_time = None,
                last_rc = 0,
                rate_limit_secs = to_secs(self._task.rate_limit_time, 60),
                retry_after_secs = to_secs(self._task.retry_after_time, 60),
                result_text = None,
                params = json_dumps(self._task.params.toDict())
            )
            self.pmdb.upsert(record)

    def exec(self):
        # hit a url using http request
        record = self.pmdb.get_where(WebApiTable, WebApiTable.name == self.name)
        if not record:
            _debug(f"record not found for {self.name}")
            return
        if record.last_time:
            elapsed = time.time() - record.last_time.timestamp()
            if elapsed < record.rate_limit_secs:
                _debug(f"rate limit not reached for {self.name}, elapsed {elapsed} secs")
                return
        try:
            params = json_loads(record.params)
            response: requests.Response = requests.get(record.url, params=params)
            rc = response.status_code
            if rc == 200:
                record.last_time = datetime.now()
                record.last_rc = rc
                record.result_text = response.text
                self.pmdb.upsert(record)
            else:
                _error(response)
                _error(response.text)
                sys.exit()
        except Exception as e:
            _debug(e)
            sys.exit()