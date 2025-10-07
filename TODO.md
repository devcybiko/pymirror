# TODO List

## Control Page

1. add control page element to clear database
1. add control page element pull from github (to facilitate config updates without rebooting)

## iCalendar

1. Handle multiple calendars
1. Add Alerts to ICal_Module

## Alerts

1. ** Force alerts to the foreground **
8. if alert card is 'timed', show timer percent. bar
22. Make multiple alerts cycle


## Configuration

6. Hot Reload of config.json
    - if config.json is updated then dispose of old modules and reload
19. add color palette to config.json

## Text

20. Make Longer "card body" text scroll
21. Add Blinking Text
26. text scrolling horizontally and vertically, blinking color

## General

1. Error Handling: Better error handling
17. add device drivers for display
25. Different display configurations need to be detected and handled (same as device drivers, above?)
31. Make the Control Panel web page display current status in the toggles (currently always shows "off")

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

### Downward/Negative Direction:

- \u2193 (↓) - Downwards arrow
- \u25BC (▼) - Black down-pointing triangle
- \u25BD (▽) - White down-pointing triangle
- \u2935 (⤵) - Arrow pointing rightwards then curving downwards

### Bad/Negative/Error:

- \u2717 (✗) - Ballot X (cross mark)
- \u2718 (✘) - Heavy ballot X
- \u274C (❌) - Cross mark
- \u274E (❎) - Negative squared cross mark
- \u26A0 (⚠) - Warning sign
- \u203C (‼) - Double exclamation mark
- \u2049 (⁉) - Exclamation question mark
- \u26D4 (⛔) - No entry sign
- \u1F6AB (🚫) - No entry sign (emoji)

### Thumbs Down:

- \u1F44E (👎) - Thumbs down sign

### Upward/Positive Direction:

- \u2191 (↑) - Upwards arrow (opposite of ↓)
- \u25B2 (▲) - Black up-pointing triangle (opposite of ▼)
- \u25B3 (△) - White up-pointing triangle (opposite of ▽)
- \u2934 (⤴) - Arrow pointing rightwards then curving upwards (opposite of ⤵)

### Good/Positive/Success:

- \u2713 (✓) - Check mark (opposite of ✗)
- \u2714 (✔) - Heavy check mark (opposite of ✘)
- \u2705 (✅) - White heavy check mark (opposite of ❌)
- \u2611 (☑) - Ballot box with check (opposite of ❎)
- \u2139 (ℹ) - Information source (opposite of ⚠)
- \u2728 (✨) - Sparkles (positive indicator)
- \u2705 (✅) - Check mark button (opposite of 🚫)

### Thumbs Up:

- \u1F44D (👍) - Thumbs up sign (opposite of 👎)

## Available insect-like glyphs:

\u1F41B (🐛) - Bug emoji
\u1F98B (🦋) - Butterfly emoji
\u1F577 (🕷) - Spider emoji
\u1F41C (🐜) - Ant emoji
\u1F41D (🐝) - Honeybee emoji
\u1FAB2 (🪲) - Beetle emoji (newer Unicode)
Note: These are emoji characters, not traditional font glyphs, so they may not display consistently across all fonts or systems.

## Alternative symbols for "bug" (as in software bug):

\u26A0 (⚠) - Warning sign
\u1F6A8 (🚨) - Police car light (alert)
\u274C (❌) - Cross mark
\u1F525 (🔥) - Fire (for critical issues)

## Debug/Development symbols:

\u1D6AB (𝚫) - Mathematical bold capital delta (often used for "change" or "debug")
\u0394 (Δ) - Greek capital letter delta (change/difference)
\u2206 (∆) - Increment (mathematical delta)
\u2699 (⚙) - Gear (settings/configuration)
\u1F527 (🔧) - Wrench (but this is an emoji)

## Better non-emoji alternatives:

\u26ED (⛭) - Gear without hub (mechanical symbol)
\u2692 (⚒) - Hammer and pick (tools)
\u26CF (⛏) - Pick (tool symbol)

## Simple text-based alternatives:

\u0044 (D) - Just use "D" for Debug
\u1D6AB (𝚫) - Mathematical bold delta
\u00A4 (¤) - Generic currency symbol (often used as placeholder)

