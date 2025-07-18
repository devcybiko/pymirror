# weather.py
# https://openweathermap.org/api/one-call-3#current

import requests
import json
from datetime import datetime
from types import SimpleNamespace
from dataclasses import dataclass
from pymirror.pmbitmap import PMBitmap
from pymirror.pmcard import PMCard
from events import AlertEvent
from pymirror.pmwebapi import PMWebApi
from pymirror.utils import SafeNamespace

@dataclass
class OpenWeatherMapConfig:
    lat: str = "37.5050"
    lon: str = "-77.6491"
    appid: str = ""
    exclude: str = "minutely"
    units: str = "imperial"
    lang: str = "english"

@dataclass
class WeatherConfig:
    url: str
    cache_file: str  = None
    cache_timeout_secs: int = 3600  # Default cache timeout in seconds
    refresh_minutes: int = 15
    degrees: str = "°F"
    datetime_format: str = "%I:%M:%S %p"
    lat: str = "37.5050"
    lon: str = "-77.6491"
    appid: str = ""
    exclude: str = "minutely"
    units: str = "imperial"
    lang: str = "english"

def _paragraph_fix(text: str) -> str:
    results = []
    paragraphs = text.split("\n\n")
    for paragraph in paragraphs:
        lines = paragraph.split("\n")
        paragraph = " ".join(line.strip() for line in lines)
        results.append(paragraph)
    return "\n\n".join(results)

class Weather(PMCard):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._weather = WeatherConfig(**config.weather.__dict__)
        self.timer.set_timeout(1)  # refresh right away
        self.weather_response = None
        self.api = PMWebApi(self._weather.url, self._weather.cache_file, self._weather.cache_timeout_secs)
        self.owm_config = OpenWeatherMapConfig(
            lat=self._weather.lat,
            lon=self._weather.lon,
            appid=self._weather.appid,
            exclude=self._weather.exclude,
            units=self._weather.units,
            lang=self._weather.lang
        )

    def exec(self) -> bool:
        is_dirty = super().exec()
        if not self.timer.is_timedout():
            return is_dirty # early exit if not timed out
        self.timer.set_timeout(self._weather.refresh_minutes * 60 * 1000)
        self.weather_response = SafeNamespace(**self.api.get_json(self.owm_config.__dict__))
        # print(f"Weather response: {self.weather_response}")  # Debugging line
        w = self.weather_response.current
        d = self.weather_response.daily
        cfg = self._weather
        # convert w.current.dt to a datetime object
        dt_str = f"({d[0].weather[0].description})\n{datetime.fromtimestamp(w.dt).strftime(cfg.datetime_format)}"
        self.update(
            "WEATHER",
            f"{w.temp}{cfg.degrees}\n{w.humidity} %\n{w.feels_like}{cfg.degrees}",
            dt_str,
        )

        if d:
            # Publish the weather data as an event
            event = {
                "event": "WeatherForecastEvent",
                "data": self.weather_response,
            }
            print(f"Publishing weather forecast event: {event['event']}")
            self.publish_event(event)

        if w.alerts:
            alerts = w.alerts
            if alerts:
                alert = alerts[0]
                event = {
                    "event": "WeatherAlertEvent",
                    "header": alert["event"],
                    "body": f"{_paragraph_fix(alert['description'])}",
                    "footer": f"Expires: {datetime.fromtimestamp(alert['end']).strftime(self._weather.datetime_format)}",
                    "timeout": self._weather.refresh_minutes * 60 * 1000
                }
                print(f"Publishing weather alert event: {event['event']}")
                self.publish_event(event)

        self.weather_response = None  # Clear response after rendering
        return True # state changed
