# pymirror

- A Python Dashboard inspired by Magic Mirror 2 
    - By Greg Smith (greg@agilefrontiers.com)
    - Created June, 2025
- Developed for low-resource RPI Zero 2 W
- Writes directly to the frame buffer using Pillow / PIL

## Installation

- RPI OS Lite 32-bit
  - `sudo apt update`
  - `sudo apt install git`
  - `git clone https://github.com/drfrancintosh/pymirror.git`
  - `sudo apt install fortune`
  - `sudo apt install libdrm-tests`
    - `modetest` (will display hardware information on the displays)
  - `sudo apt install calendar`
  - `sudo apt install python3-setuptools`
  - `sudo apt-get install python3-venv python3-full`
- Python Virtual Environment
  - `cd pymirror`
  - `python3 -m venv .venv --system-site-packages`
  - `source .venv/bin/activate`
  - Calendar (here? maybe better in the install_libs.sh)
  - `pip install ics`

## Installing Libraries

- NOTE: Need separate Windows/Linux/Macos/RPi install instructions
- RPi OS:
  - `source ./scripts/install-libs.sh`
  - `pip install -r requirements.txt`


## Create ".secrets" file
- see the ./secrets file
- add your API keys to `.secrets`
  - (Note be confused with the ./secrets sample file)
  
## Build HDMI screen custom device driver
- MacOS Homebrew Python
  - `brew install python@3.13-dev`
  - Or reinstall Python with dev headers
  - `brew reinstall python@3.13`
- RPi
  - `sudo apt-get install python3.11-dev`
- Run python setup.py
  - `cd src/clib`
  - `python3 setup.py build_ext --inplace`

## Running

- `cd ./pymirror`
- `./run.sh`


## Fontlist.txt

- One font per line
- Basically the output of `fc-list`
- add your own fonts as well
- Star Trek fonts in the `fonts` folder were appropriated from https://www.st-minutiae.com/resources/fonts/index.html
- There were no credits there, but if anyone knows who to credit, I'll add the credits here
- The 7segment.txt font was from https://torinak.com/font/7-segment
- The Default font DejaVuSerif.ttf was delivered with RPI-OS and copied locally for convenience
- The Roboto fonts came from https://fonts.google.com/specimen/Roboto
- Update `fontlist.txt` as per your system
- Icons fonts (Font Awesome) Free download
  - https://fontawesome.com/search?o=r&s=solid&ip=classic
  - https://fontawesome.com/search?o=r&s=regular&ip=classic
  - https://fontawesome.com/search?ic=brands

## Images folder

- Thanks to `https://github.com/yavuzceliker/sample-images` for sample images

## Web Server

- GET: `http://rpi01:8080`
    - serves up HTML pages that allow you to control your PyMirror
- POST: `http://rpi01:8080/command`
    - will allow you to publish an `event` directly to PyMirror
    - All "subscribed" modules will receive the event 
    - the payload is event-specific...
    - Here is an example for the `alert` module
```json
{
    "name": "weather_alert",
    "heading": "Hello PyMirror!",
    "body": "This is your first PyMirror event",
    "footer": "(C) 2025",
    "timeout": 10000
}
```

## Folders

- caches/ - last calls from the web api in case the api is down and in the case that that PyMirror is calling faster than the rate limit
- configs/ - .json config files (one per dashboard)
  - digital_frame/ - a simple frame + slideshow and nothing else
  - gls/ - my personal pymirror config
  - macos/ - macos test config
  - mm2/ - magic mirror look-alike config
  - rpi/ - "production" delivered configuration
  - test/ - simple test config
- fonts/ - local .ttf files
- frames/ - images for slideshow frames
- random/ - test code and other fancy biscuits
- samples/ - web api samples
- scripts/ - test scripts
- sounds/ - .wav files the play
- src/
  - clib/ - 'c' code that improves Python performance
  - events/ - python definition of PyMirror events
  - modules/ - PyMirror modules
  - pmgfxlib/ - Python wrapper code to isolate bit-mapped graphics
  - pmsever/ - the flask web server class and other files (html, etc...)
  - pymirror/ - pymirror python source files
- weather_icons/ - for the forecast module

## Files

- .env - list of environment variables in KEY=value format (ignored by .gitignore, read into the PyMirror os.environ)
- .secrets - list of API keys in KEY=value format (ignored by .gitignore, read into the PyMirror os.environ)
- fontlist.txt - PyMirror list of fonts and where to find them
- README.md - this file
- requirements.txt - list of Python packages needed to support PyMirror and the default modules
- run.debug - script to run PyMirror locally (writing to .jpeg) and dribble logs to console
- run.sh - script to run PyMirror (/dev/fb0 and quiet logs)
- secrets - sample .secrets file
- TODO.md - wish list of things to add to PyMirror

## Modules

- Modules are stored in the `./src/modules` folder
- The name of the Python file must be the snake-case version of the camel-case name of the module class and end in _module.
  - example: `analog_clock_module.py` -> `AnalogClockModule` (class name for the module)
- In the `config.json` you can call up a module multiple times with different instances
  - but not using the `_module` part of the filename
  - example: `"module": "analog_clock"`

- weather_apis/ - folder holding interfaces to weather apis (accuweather, openwathermap)
- alert_module.py
  - displays alerts as a card (header, body, and footer). Subscribed to AlertEvent which updates the alert
- analog_clock_module.py
  - Displays analog clock (round face)
- caldav_module.py
  - displays "CALDAV" calendar api
- cli_module.py
  - Runs a CLI command on a timer and displays the results
- clock_module.py
  - Displays current time as strftime() format, 
- complements_module.py
  - Displays a random compliment
- cron_module.py
  - no display, but runs on a timer and sends the defined event
- fonts_module.py
  - list of fonts in fontlist.txt
- forecast_module.py
  - accepts a WeatherForecast event and displays the results in a Card
- fps_module.py
  - DEBUG: Frames Per Second display
- ical_module.py
  - displays ical web api calendar
- photo_module.py
  - displays a single photo
- pymirror_controller_module.py
  - handles and dispatches external events
- rainbow_module.py
  - test pattern showing all colors in RGB Bands
- slideshow_module.py
  - shows images in a cycle
- sound_module.py
  - plays sounds in reaction to SoundEvent events
- text_module.py
  - displays static text
- weather_module.py
  - Displays current temperature, humidity, and effective temperature (accuweather or openweathermap)
- web_api_module.py
  - sends a web request and displays the formatted payload

## config.json

```json
{
  "debug": false, // when true displays boxes around module 'windows'
  "secrets": ".secrets", // your API keys and other secrets
  "force_render": false, // forces a render of all modules regardless of state changes
  "screen": {
    "output_file": null, // optional output file for use in debugging or html display
    "frame_buffer": "/dev/fb0", // frame buffer device (esp. rpi 02w)
    "font_name": "Roboto-Thin", // default font used when modules do not specify a font
    "font_size": 64, // default font size
    "color": "#fff", // default line color
    "bg_color": "#000", // default fill color
    "text_color": "#fff", // default text color
    "text_bg_color": null // default text background color
  },
  "positions": {
    // A list of rectangles on the display in "percentage" of screen geometry 
    "None": "0.0,0.0,0.0,0.0", // used by non-displaying modules (cron, pymirror_controller, eg)
    "top_strip": "0.00,0.0,1.0,0.15", // format is (x0, y0, x1, y1) where values are 0.0 up to 1.0
    "alert_strip": "0.30,0.30,0.7,0.7", // note that this one overlays others. also note that the 'position' is tied to the module name
    "fps_strip": "0.0,0.95,0.33,1.00", // fps module location. in future it may be better to specify the module position rather than the relative positions like "top_left", etc...
    "top_left": "0.0,0.15,0.33,0.33",
    "top_center_left": "0.33,0.15,0.55,0.33",
    "top_center_right": "0.55,0.15,0.66,0.33",
    "top_right": "0.66,0.15,1.00,0.33",
    "middle_left": "0.0,0.33,0.33,0.66",
    "middle_center": "0.33,0.33,0.66,0.85",
    "middle_right": "0.66,0.33,1.00,1.00",
    "bottom_left": "0.0,0.66,0.33,1.00",
    "bottom_center": "0.33,0.85,0.66,1.00",
    "bottom_right_center": "0.7,0.66,1.00,0.90",
    "bottom_right": "0.66,0.90,1.00,1.00"
    },
  "modules": [
    "moddefs/alert.json", // an alert displayed by way of an AlertEvent
    "moddefs/pymirror_controller.json", // the controller for external events
    "moddefs/weather.json", // displays current temperature and weather alerts (OpenWeatherMap API)
    "moddefs/fortune.json", // runs linux 'fortune' command every 15 secs
    "moddefs/news.json", // displays news using web_api module
    "moddefs/date.json", // displays the current date in 7-segment display font
    "moddefs/time.json", // displays the current time in 7-segment display font
    "moddefs/week.json", // displays the word "Week:" - static text
    "moddefs/day_of_week.json", // displays the current day of the week
    "moddefs/week_of_year.json", // displays the week number (1-52)
    "moddefs/analog_clock.json", // analog clock
    "moddefs/weather_alert.json", // an alert box for any weather alerts that are received by the alert module
    "moddefs/fps.json", // displays the Frames Per Second calculation
    // NOTE: you may also put full module definitions right here as a json dictionary
    {
      "module": "fps",
      "moddef": {
        "disabled": false,
        "name": "fps",
        "position": "fps_strip",
        "font_size": 32
      },
      "fps": {
        "valign": "bottom",
        "halign": "left"
      }
    }
  ]
}

```

## Module Definition Files (./configs/rpi/*.json)
- Module Definitions identify the module class and the parameters to display the module
- Not that that a module (like Date) may be instantiated many times.
- Each with a different ModDef (see date.json, day_of_week.json, time.json, week_of_year.json) 
```json
{
    "module": "alert", // module name. must be lowercase and reside in src/modules/alert_module.py
    "moddef": { // all modules have a required generic module definition or 'moddef'
        "name": "Alert", // a unique name
        "position": "alert_strip", // a position defined in config.json, the 'positions' section
        "text_color": null, // default text color - overrides config.json if non-null
        "text_bg_color": null, // default text background color - overrides config.json if non-null
        "font_name": "TNG_Title", // font name definined in fontlist.txt
        "font_size": 24, // default font size
        "subscriptions": ["AlertEvent"], // any events this module is 'subscribed' to
        "force_render": false // when true, forces rendering despite no changes in stateful informaton
    },
    "alert": { // every module has module-specific information that is the same name as the name of the module
        "header": "Alert", // this module uses the 'card' format which has a header, footer, and body
        "body": "This is an alert message.", // these are the default text values for header, footer, and body
        "footer": "Alert Footer",
        "timeout": 2000 // when specified, this is the duration of the alert. 0 == disabled
    },
    "card": { // when a module is a subclass of a 'PMCard', the config will be found inside a 'card' dict. not all modules have this
        "header": {
            "font_name": "TNG_Credits",
            "font_size": 24,
            "text_color": "#000",
            "text_bg_color": "#0ff",
            "height": 48
        },
        "body": {
            "font_name": "TNG_Credits",
            "font_size": 24,
            "text_color": "#ff0",
            "text_bg_color": "#333"
        },
        "footer": {
            "font_name": "DejaVuSans",
            "font_size": 24,
            "text_color": "#000",
            "text_bg_color": "#fff",
            "height": 48
        }
    }
}
```
## Bump
