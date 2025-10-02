# pip install caldav vobject
import os
from caldav import DAVClient
import vobject, datetime as dt, pytz
import dotenv
from pymirror.pmlogger import _debug

dotenv.load_dotenv(".secrets")
APPLE_ID_EMAIL = os.getenv("APPLE_ID_EMAIL")
APPLE_CALDEV_PASSWORD = os.getenv("APPLE_CALDEV_PASSWORD")
client = DAVClient(url="https://caldav.icloud.com", username=APPLE_ID_EMAIL, password=APPLE_CALDEV_PASSWORD)
principal = client.principal()
cals = principal.calendars()

# ...existing code...

import datetime as dt

# Get current time and 3 months ahead
# ...existing code...

now = dt.datetime.now(pytz.utc)
three_months_later = now + dt.timedelta(days=90)

for c in cals:
    _debug("Calendar:", c.name)
    events = c.date_search(start=now, end=three_months_later)
    parsed_events = []
    for event in events:
        try:
            vcal = vobject.readOne(event.data)
            vevent = vcal.vevent
            summary = getattr(vevent, 'summary', None)
            dtstart = getattr(vevent, 'dtstart', None)
            dtend = getattr(vevent, 'dtend', None)
            # Normalize start_time to datetime.datetime
            start_time = dtstart.value if dtstart else now
            if isinstance(start_time, dt.date) and not isinstance(start_time, dt.datetime):
                # All-day event: convert to datetime at midnight, use UTC or calendar's tz if available
                tz = pytz.utc
                if hasattr(dtstart, 'params') and 'TZID' in dtstart.params:
                    try:
                        tz = pytz.timezone(dtstart.params['TZID'][0])
                    except Exception:
                        pass
                start_time = tz.localize(dt.datetime.combine(start_time, dt.time()))
            parsed_events.append((start_time, summary, dtstart, dtend))
        except Exception as e:
            _debug("    Error parsing event:", e)
    # Sort events by normalized start_time
    parsed_events.sort(key=lambda tup: tup[0])
    _debug(f"  {len(parsed_events)} events in next 3 months (sorted):")
    for start_time, summary, dtstart, dtend in parsed_events:
        _debug("    Event:", summary.value if summary else "(no summary)")
        _debug("      Start:", dtstart.value if dtstart else "(no start)")
        _debug("      End:", dtend.value if dtend else "(no end)")
