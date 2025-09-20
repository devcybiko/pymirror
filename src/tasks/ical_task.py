from datetime import datetime
from sqlalchemy.exc import IntegrityError
from icecream import ic
from sqlalchemy import Column, DateTime, Integer, String
from pmdb.pmdb import Base
from sqlalchemy.orm import declarative_base

from pmtaskmgr.pmtask import PMTask
from pymirror.utils import make_naive, make_hashcode, to_munch
from pymirror.pmlogger import _debug
from pymirror.ical_parser import IcalParser
import requests

Base = declarative_base()

class IcalTable(Base):
    __tablename__ = 'ical'
    id = Column(Integer, primary_key=True)
    calendar_name = Column(String)
    all_day = Column(String)
    dtend = Column(DateTime)
    dtstart = Column(DateTime)
    summary = Column(String)
    description = Column(String)
    rrule = Column(String)
    uid = Column(String, unique=True)

class IcalTask(PMTask):
    def __init__(self, pmtm, config):
        super().__init__(pmtm, config)
        self.pmdb.create_table(IcalTable, checkfirst=True, force=False)
        self.url = self._task.url
        self.calendar_name = self._task.calendar_name

    def _add_new_events(self, events):
        for _event in events:
            _event["uid"] = make_hashcode(_event["dtstart$"], _event["dtend$"], _event["all_day"], _event["summary"], _event["description"])
            event = to_munch(_event)
            record = IcalTable(
                calendar_name = self.calendar_name,
                all_day = event.all_day,
                dtend=make_naive(event.dtend),
                dtstart=make_naive(event.dtstart),
                summary=event.summary,
                description=event.description,
                rrule=event.rrule,
                uid=event.uid
            )
            try:
                self.pmdb.upsert(record)
            except IntegrityError as e:
                    ## it's okay - duplicate entries are ignored
                    continue
            else:
                print("ADDED:", record.uid, record.summary, record.description)


    def _remove_deleted_events(self, events):
        ## GLS: Need to handle special case of individual dates removed from repeating events
        event_uids = [event["uid"] for event in events]
        records = self.pmdb.get_all(IcalTable)
        for record in records:
             if record.uid not in event_uids:
                  print("REMOVING:", record.uid, record.summary, record.description)
                  self.pmdb.delete(record)
             pass

    def exec(self):
            response: requests.Response = requests.get(self.url)
            rc = response.status_code
            if rc == 200:
                ical_parser = IcalParser(response.text.splitlines())
                now = datetime.now().strftime("%Y-%m-%d")
                then = "2100-12-31"
                events = ical_parser.parse(now, then)
                self._add_new_events(events)
                self._remove_deleted_events(events)
            sys.exit()
            return
