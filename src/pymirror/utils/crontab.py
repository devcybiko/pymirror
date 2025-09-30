import datetime
import sys

from pymirror.utils.utils import has_alpha, to_int, to_list
from pymirror.pmlogger import _debug, _print

_SECONDS=0 # seconds index
_MINUTES=1 # minutes index
_HOURS=2 # hours index
_DAY=3 # day index
_MONTH=4 # month index
_DOW=5 # day-of-week index
_RETURN_STRING=6 # return string (after '|' ) if specified
class Crontab:
    def __init__(self, crontab: list[str]):
        # crontab is a list of classic 'cron' patterns ([secs] mins hours day month dow)
        # plus the cron pattern can have a '|' that is a string to return on matching
        self.crontab = self._init_cronlist(to_list(crontab) or [])
        self.cronparts_list = [self._parse_cronstring(cron) for cron in self.crontab]
        self.last_crontime = None
        self.crontime = self._update_crontime()
        self.cron_now = None

    def check(self, _cron_now: list[int] = None) -> list[int]:
        """returns a list of indices of crontabs that match the current time"""
        results = []
        self._update_crontime()
        if self.crontime == self.last_crontime:
            ## it hasn't been at least 1 second...
            return results
        self.last_crontime = self.crontime
        self.cron_now = _cron_now or self._to_cron_int(self.crontime)
        for i in range(len(self.cronparts_list)):
            if self._compare_cronparts(self.cronparts_list[i]):
                if self.cronparts_list[i][_RETURN_STRING]:
                    results.append(self.cronparts_list[i][_RETURN_STRING])
                else:
                    results.append(i)
        return results

    def _convert_slash_date_string(self, date_string: str) -> str:
        words = date_string.lower().split("/")
        year = "*"
        month = "*"
        day = "*"
        if len(words) == 1:
            ## assume it's a date specifier
            year = "*"
            month = "*"
            day = to_int(words[0], words[0])
        if len(words) == 2:
            ## assume it's a month/day specifier
            year = "*"
            month = to_int(words[0], words[0])
            day = to_int(words[1], words[1])
        if len(words) == 3:
            ## assume it's a month/day/year specifier
            month = to_int(words[0], words[0])
            day = to_int(words[1], words[1])
            year = to_int(words[2], words[2])
        return f"{day} {month}".strip()

    def _convert_dash_date_string(self, date_string: str) -> str:
        words = date_string.lower().split("-")
        year = "*"
        month = "*"
        day = "*"
        if len(words) == 1:
            ## assume it's a day specifier
            year = "*"
            month = "*"
            day = to_int(words[0], words[0])
        if len(words) == 2:
            ## assume it's a month-day specifier
            year = "*"
            month = to_int(words[0], words[0])
            day = to_int(words[1], words[1])
        if len(words) == 3:
            ## assume it's a year-month-day specifier
            year = to_int(words[0], words[0])
            month = to_int(words[1], words[1])
            day = to_int(words[2], words[2])
        return f"{day} {month}".strip()

    def _convert_date_string(self, date_string: str) -> str:
        if "-" in date_string:
            return self._convert_dash_date_string(date_string)
        if "/" in date_string:
            return self._convert_slash_date_string(date_string)
        return date_string

    def _convert_time_string(self, time_string: str) -> str:
        """Convert a time string to a datetime object."""
        _debug(f"Converting time string:", time_string)
        words = time_string.lower().split(":")
        hour = "*"
        minute = "*"
        seconds = "0"
        if len(words) == 1:
            _debug(f"Parsed hour:", hour)
            hour = to_int(words[0], words[0])
        if len(words) == 2:
            _debug(f"Parsed hour:minute:", hour, minute)
            hour = to_int(words[0], words[0])
            minute = to_int(words[1], words[1])
        if len(words) == 3:
            _debug(f"Parsed hour:minute:seconds:", hour, minute, seconds)
            hour = to_int(words[0], words[0])
            minute = to_int(words[1], words[1])
            seconds = to_int(words[2], words[2])
        return f"{seconds} {minute} {hour}".strip()

    def _convert_dow_string(self, dow_string: str) -> str:
        """Convert a day of week string to a datetime object."""
        words = dow_string.split(",")
        days = []
        dow = {
            "mon": 1,
            "m": 1,
            "tue": 2,
            "tues": 2,
            "t": 2,
            "wed": 3,
            "weds": 3,
            "w": 3,
            "thu": 4,
            "thurs": 4,
            "r": 4,
            "fri": 5,
            "f": 5,
            "sat": 6,
            "sa": 6,
            "sun": 0,
            "su": 0,
        }
        for word in words:
            days.append(dow[word])
        if not days:
            return "*"
        _debug("days", days)
        return ",".join(map(str, days))

    def _init_cronlist(self, cron_strings: list[str] = []):
        crontab = []
        for _cron_string in cron_strings:
            parts = _cron_string.split("|", 1)
            cron_string = parts[0]
            return_string = "" if len(parts) < 2 else parts[1].strip()
            try:
                cron_string = cron_string.lower().strip()
                if "-" in cron_string or ":" in cron_string or "/" in cron_string:
                    date_str = "* *"
                    time_str = "0 0 0"
                    dow_str = "*"
                    parts = cron_string.split(" ")
                    _debug(parts)
                    for part in parts:
                        if "-" in part or "/" in part:
                            date_str = self._convert_date_string(part)
                            _debug("date_str", date_str)
                        elif ":" in part:
                            time_str = self._convert_time_string(part)
                            _debug("time_str", time_str)
                        else:
                            dow_str = self._convert_dow_string(part)
                            _debug("dow_str", dow_str)
                    cron_string = time_str + " " + date_str + " " + dow_str
                if has_alpha(cron_string):
                    raise Exception("Cron string contains invalid characters")
                crontab.append(cron_string + "|" + return_string)
            except Exception as e:
                print(f"Error processing cron string: {cron_string}|{return_string}")
                sys.exit(1)
        return crontab

    def _update_crontime(self):
        # Get current time with second resolution only
        self.crontime = datetime.datetime.now().replace(microsecond=0)
        return self.crontime

    def _to_cron_int(self, now) -> list:
        weekday = (now.weekday() + 1) % 7
        result = [now.second, now.minute, now.hour, now.day, now.month, weekday]
        return result

    def _parse_cronstring(self, cronstring) -> list[list[str]]:
        result = []
        parts = cronstring.split("|", 1)
        cron_parts = parts[0].split(" ")
        return_string = parts[1].strip()
        while len(cron_parts) < 6:
            ## if seconds were not specified, default to 00 seconds
            cron_parts = ["0"] + cron_parts
        for cron_part in cron_parts:
            result.append(cron_part.split(","))
        result.append(return_string)
        return result

    def _compare_cronparts(self, cron_parts: list[list[str]]) -> bool:
        for i in range(6):
            if i == _DOW and ("*" not in cron_parts[_DAY]):
                ## special case: if a day was specified, don't do day-of-week matching
                continue
            for digit in cron_parts[i]:
                ## handle pattern matching on comma-separated values
                if digit == "*":
                    ## wild card matches anything
                    _debug(f"{digit}={self.cron_now[i]} Wildcard match found")
                    break
                digit = to_int(digit, -1)
                if digit == self.cron_now[i]:
                    _debug(f"{digit}={self.cron_now[i]} matches")
                    break
            else:
                _debug(
                    f"{i}: Cron part {cron_parts[i]} did not match {self.cron_now[i]}"
                )
                return False
        _debug(f"{i}: All cron parts matched successfully")
        return True


if __name__ == "__main__":
    crontab = [
        "* * * * *",
        "0,15,30,45 * * * *",
        "12:00,05,10,15:30",
        "*:0,15,30,45:30",
        "*:00 m,t,w,r,f",
        "12/04/2025",
        "2025-12-04 m,t,w,r,f",
        "12/04 12:00",
        "04/04 12:00:00",
        "12:00:00 m,t,w,r,f",
        "*:00",
        "*:15,30,45",
        "17:00:00",
        "00:00 m,t,w,r,f",
        "*:*:0,5,10,15,20,25,30,35,40,45,50,55"
    ]
    expected = [
        "* * * * *",
        "0,15,30,45 * * * *",
        "30 00,05,10,15 12 * * *",
        "30 0,15,30,45 * * * *",
        "0 0 * * * 1,2,3,4,5",
        "0 0 0 4 12 *",
        "0 0 0 4 12 1,2,3,4,5",
        "0 0 12 4 12 *",
        "0 0 12 4 4 *",
        "0 0 12 * * 1,2,3,4,5",
        "0 0 * * * *",
        "0 15,30,45 * * * *",
        "0 0 17 * * *",
        "0 0 0 * * 1,2,3,4,5",
        "0,5,10,15,20,25,30,35,40,45,50,55 * * * * *"
    ]
    print("Crontab test")
    cron = Crontab(crontab)
    for i in range(len(cron.crontab)):
        if cron.crontab[i] == expected[i]:
            print("...", crontab[i], "=>", cron.crontab[i])
        else:
            print("ERROR:", crontab[i], "=>", cron.crontab[i], "Expected:", expected[i])

    times = [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [0, 0, 0, 4, 12, 0],
        # [0, 0, 0, 1, 0, 0],
        # [0, 0, 1, 0, 0, 0],
        # [0, 1, 0, 0, 0, 0],
        # [1, 0, 0, 0, 0, 0],
    ]
    for time in times:
        matches = cron.check(time)
        cron.last_crontime = None
        if not matches:
            print(time, "none matches:")
        for i in matches:
            print("match:", i, time, cron.crontab[i])