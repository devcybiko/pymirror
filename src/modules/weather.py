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
from .weather_apis.pmweatherdata import PMWeatherData

@dataclass
class WeatherConfig:
    refresh_minutes: int = 15
    degrees: str = "°F"
    datetime_format: str = "%I:%M:%S %p"


class Weather(PMCard):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._weather = WeatherConfig(**config.weather.__dict__)
        self.timer.set_timeout(1)  # refresh right away
        self.weather_response = None
        if config.openweathermap:
            from .weather_apis.openweathermap import OpenWeatherMapApi
            self.api = OpenWeatherMapApi(config.openweathermap)
        elif config.accuweather:
            from .weather_apis.accuweather import AccuWeatherApi
            self.api = AccuWeatherApi(config.accuweather)

    def exec(self) -> bool:
        is_dirty = super().exec()
        if not self.timer.is_timedout(): return is_dirty # early exit if not timed out

        self.timer.set_timeout(self._weather.refresh_minutes * 60 * 1000)
        self.weather_response = self.api.get_weather_data()
        weather = self.weather_response.current
        daily = self.weather_response.daily
        alerts = self.weather_response.alerts
        cfg = self._weather
        # convert w.current.dt to a datetime object
        dt_str = f"({daily[0].weather[0].description})\n{datetime.fromtimestamp(weather.dt).strftime(cfg.datetime_format)}"
        self.update(
            self.api.config.name,
            f"{weather.temp}{cfg.degrees}\n{weather.humidity} %\n{weather.feels_like}{cfg.degrees}",
            dt_str,
        )

        if daily:
            # Publish the weather data as an event
            event = {
                "event": "WeatherForecastEvent",
                "data": self.weather_response,
            }
            print(f"Publishing weather forecast event: {event['event']}")
            self.publish_event(event)

        if alerts:
            alert = alerts[0]
            event = {
                "event": "WeatherAlertEvent",
                "header": alert.event,
                "body": alert.description,
                "footer": f"Expires: {datetime.fromtimestamp(alert.end).strftime(self._weather.datetime_format)}",
                "timeout": self._weather.refresh_minutes * 60 * 1000
            }
            print(f"Publishing weather alert event: {event['event']}")
            self.publish_event(event)

        self.weather_response = None  # Clear response after rendering
        return True # state changed
