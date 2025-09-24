# TODO List

## MVP - before launch on Dr. Francintosh

## Other Notes

- add github ssh private key to .ssh
- eval "$(ssh-agent -s)"
- ssh-add ~/.ssh/id_rsa
- ssh -T git@github.com

## Special Commands
- vcgencmd get_throttled
- vcgencmd get_config int
- dmesg -w

## .bashrc
echo "PyMirror Started"
setterm -cursor off 
cd git/pymirror
./run.sh

## Running Module Tests

- `PYTHONPATH=./src python -m pymirror.pmwebapi`

## Backlog

### Calendar

1. Handle Week starting on Monday vs Sunday
1. Handle work week 
1. Handle multiple calendars

1. BUG? The cached news is lasting >120 minutes. And it is only showing 10 elements
1. News items rotating faster than 30 seconds?
1. Change color of News Headline to something brighter/bolder/ more readable
1. add control page element to clear cache
1. add control page element to restart the pymirror and pull from github (to facilitate config updates without rebooting)
1. Fix headers on Weather Module
1. Add Alerts to ICal_Module
8. if alert card is 'timed', show timer percent. bar
6. Hot Reload of config.json
    - if config.json is updated then dispose of old modules and reload
1. Error Handling
    1. weather.py - error checking for bad api results
    1. Better error handling
17. add device drivers for display
18. switch to JSON5 for easier JSON editing.
19. add color palette to config.json
20. Make Longer "card body" text scroll
21. Add Blinking Text
22. Make multiple alerts cycle
23. need to add "force" on an option for a module like "alert" so it always show up on top
24. For "positions" allow aliases: "fps_strip": "bottom_left" so that moddefs are not tied to screen positions
25. Different display configurations need to be detected and handled (same as device drivers, above?)
26. text scrolling horizontally and vertically, blinking color
27. Add strong typing and checks on config data
30. Better solution for web-based logging (dribbling stderr/stdout to text file is not a good solution)
31. Make the Control Panel web page display current status in the toggles (currently always shows "off")

## DONE

1. Add "clear memory cache" and "clear file cache" to control panel
1. Switch Raspberry PI to PIP rather than APP GET
1. update gfx object so "set_font(font_name, font_size)" is 'permanent'
    - currently it only sets the gfx.font, but not gfx.font_name, gfx.font_size
    - likewise remove reset_font()
    - originally the idea was set_font() would temporarily set the font and reset_font() would restore it
    - but with gfx = copy.copy(self.gfx) we can manipulate the gfx obj and font and not worry about resetting
3. exec() should return True if a render() is needed and False otherwise
4. render() should be called only if exec() returns True
5. render()
    - render(force=True) implies a full re-rendering (clear the old, redraw the new)
    - render(force=False) implies a minimal repaint of only what has updated since the last render
    - it is up to the module to determine what needs updating
8. Convert all forms of color to 32-bit integer for use in PIL "I" mode
9. Handle Portrait mode
11. text_box() needs text_wrap abilities
    - None (just a straight line of text)
    - Wrap (split on character boundaries)
    - Word Wrap (split on word boundaries)
    - Handle (or ignore) newlines
    - Boundary clipping
13. Update screen.draw() methods to accept tuples rather than parms
14. Move configurations to separate files
15. Add webserver to control modules via events
14. Add generalized class for "window" that has header/body/footer (PMCard)
16. shore-up event processing with "onEventName()" events (can be overridden by overriding onEvent())
17.  display write-to-file and webserver
2. refresh the entire display based upon some event
     this means clearing the display and forcing all objects to re-render
7. Some sort of full refresh. PyMirror would clear the screen and all render methods would be called with "force=True"
1. add try/catch surrounding PyMirror main loop to catch errors in module processing
20. add text animations, like fade in / fade out - commented out
12. Boundary clipping
2. webserver
    1. debug on / off
    2. send alert
    3. turn on / off preview
10. optimize API calls (cache to disk) for weather, news
1. fix week number (use iso date)
7. Check on news module - "None" and missing data sometimes
7. update debug mode to include times for rendering modules
8. temporary: send output from ./run.sh to a log file 
- potentially make accessible from web front end
28. Better logging (_debug, _info, _warn, _error) at the module level
29. Add sound - weather alerts for example
6. WebServer seems to lag - lacking CPU time?
7. Generic Text Item

## ical Recurring events

RRULE Parameters
Parameter	Values/Description
FREQ	SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY
UNTIL	Date/time (e.g., UNTIL=20250131T235959Z) — last possible occurrence
COUNT	Integer (e.g., COUNT=10) — total number of occurrences
INTERVAL	Integer (e.g., INTERVAL=2) — every N units of FREQ
BYSECOND	List of seconds (0–59) (e.g., BYSECOND=0,15,30,45)
BYMINUTE	List of minutes (0–59) (e.g., BYMINUTE=0,30)
BYHOUR	List of hours (0–23) (e.g., BYHOUR=9,17)
BYDAY	List of days (e.g., BYDAY=MO,TU,WE,TH,FR,SA,SU or BYDAY=1MO,-1SU)
BYMONTHDAY	List of days in month (1–31 or -31–-1) (e.g., BYMONTHDAY=10,15,-1)
BYYEARDAY	List of days in year (1–366 or -366–-1) (e.g., BYYEARDAY=100,-1)
BYWEEKNO	List of week numbers (1–53 or -53–-1) (e.g., BYWEEKNO=20,40)
BYMONTH	List of months (1–12) (e.g., BYMONTH=1,6,12)
BYSETPOS	List of occurrence positions (e.g., BYSETPOS=1,-1)
WKST	Week start day (MO, TU, etc.; default is MO)

Negative values in RRULE parameters like BYDAY, BYMONTHDAY, BYYEARDAY, and BYWEEKNO indicate counting backwards from the end of the period (month, year, or week).

Examples:
BYMONTHDAY=-1
The last day of the month.

BYMONTHDAY=-2
The second-to-last day of the month.

BYDAY=-1SU
The last Sunday of the period (e.g., month).

BYYEARDAY=-1
The last day of the year (December 31).

BYWEEKNO=-1
The last week of the year.


## Some Unicode Glyphs

## Downward/Negative Direction:

- \u2193 (↓) - Downwards arrow
- \u25BC (▼) - Black down-pointing triangle
- \u25BD (▽) - White down-pointing triangle
- \u2935 (⤵) - Arrow pointing rightwards then curving downwards

## Bad/Negative/Error:

- \u2717 (✗) - Ballot X (cross mark)
- \u2718 (✘) - Heavy ballot X
- \u274C (❌) - Cross mark
- \u274E (❎) - Negative squared cross mark
- \u26A0 (⚠) - Warning sign
- \u203C (‼) - Double exclamation mark
- \u2049 (⁉) - Exclamation question mark
- \u26D4 (⛔) - No entry sign
- \u1F6AB (🚫) - No entry sign (emoji)

## Thumbs Down:

- \u1F44E (👎) - Thumbs down sign

## Upward/Positive Direction:

- \u2191 (↑) - Upwards arrow (opposite of ↓)
- \u25B2 (▲) - Black up-pointing triangle (opposite of ▼)
- \u25B3 (△) - White up-pointing triangle (opposite of ▽)
- \u2934 (⤴) - Arrow pointing rightwards then curving upwards (opposite of ⤵)

## Good/Positive/Success:

- \u2713 (✓) - Check mark (opposite of ✗)
- \u2714 (✔) - Heavy check mark (opposite of ✘)
- \u2705 (✅) - White heavy check mark (opposite of ❌)
- \u2611 (☑) - Ballot box with check (opposite of ❎)
- \u2139 (ℹ) - Information source (opposite of ⚠)
- \u2728 (✨) - Sparkles (positive indicator)
- \u2705 (✅) - Check mark button (opposite of 🚫)

## Thumbs Up:

- \u1F44D (👍) - Thumbs up sign (opposite of 👎)
