from datetime import datetime, timezone
import json
from sys import stderr

class IcalParser:
    def __init__(self, lines):
        self.lines = lines
        pass

    def parse(self, start_date, end_date):
        self.results = []
        self._parse_lines(self.lines, 0, start_date, end_date)
        self.results = sorted(self.results, key=lambda event: event["dtstart$"])
        return self.results

    def _parse_line(self, lines, i) -> tuple[int, str]:
        line = lines[i]
        i += 1
        while i < len(lines) and lines[i] and lines[i][0] == ' ':
            line += lines[i][1:]
            i += 1
        return i, line

    def _parse_datetime(self, dtstr):
        zulu = False
        if dtstr.endswith("Z"):
            dtstr = dtstr[:-1]
            zulu = True
        if "T" in dtstr:
            dt = datetime.strptime(dtstr, "%Y%m%dT%H%M%S")
        else:
            dt = datetime.strptime(dtstr, "%Y%m%d")
        if zulu:
            dt = dt.replace(tzinfo=timezone.utc).astimezone()  # Convert to local time
        else:
            # Make all-day events timezone-aware (local time)
            dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
        return dt, dt.isoformat()    

    def _parse_keyword(self, event, keyword0, keyword1):
        return event.get(keyword0, event.get(keyword1, ":")).split(":", 1)[1]

    def _parse_event(self, event):
        dtend = self._parse_keyword(event, "DTEND:", "DTEND;")
        dtstart = self._parse_keyword(event, "DTSTART:", "DTSTART;")
        event["all_day"] = not ("T" in dtend)
        event["dtend"], event["dtend$"] = self._parse_datetime(dtend)
        event["dtstart"], event["dtstart$"]= self._parse_datetime(dtstart)
        event["summary"] = self._parse_keyword(event, "SUMMARY:", "SUMMARY;")
        event["description"] = self._parse_keyword(event, "DESCRIPTION:", "DESCRIPTION;")
        event["rrule"] = self._parse_keyword(event, "RRULE:", "RRULE;")
        return event

    def _parse_lines(self, lines, i, start_date, end_date) -> tuple[int, dict]:
        event = {}
        while i < len(lines):
            i, line = self._parse_line(lines, i)
            if not line: 
                i += 1
                continue
            if line == "BEGIN:VEVENT":
                event = {}
            elif line == "END:VEVENT":
                event = self._parse_event(event)
                # print(start_date, event.get("dtstart", ""), event.get("dtend", ""), end_date, file=stderr)
                if start_date <= event.get("dtstart$", "") and event.get("dtend$", "") <= end_date:
                        # print(event)
                        self.results.append(event)
                event = {}
            else:
                tokens = ["RRULE:","DTSTART;","DTEND;","DTSTART:","DTEND:","SUMMARY;","SUMMARY:","DESCRIPTION:","DTSTAMP:"]
                for token in tokens:
                    if line.startswith(token):
                        event[token] = line
        return 0, 0



def main():
    def json_default(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    with open("./caches/ical2.json", 'r', encoding='utf-8') as file:
        text = file.read()
    ical_parser = IcalParser(text.split("\n"))
    result = ical_parser.parse("2025-08-01", "2025-12-31")
    print(json.dumps(result, indent=2, default=json_default), file=stderr)

if __name__ == "__main__":
    main()