from dataclasses import dataclass
from datetime import datetime
from logging import config

from flask import json
from pymirror.pmwebapi import PMWebApi
from utils.utils import SafeNamespace, json_dumps
from .pmweatherdata import PMWeatherData, PMWeatherSummary
from pymirror.pmlogger import _debug

@dataclass 
class AccuWeatherParams:
    apikey: str = ""
    lat: str = "37.5050"
    lon: str = "-77.6491"
    language: str = "en-us"
    units: str = "imperial"

@dataclass
class AccuWeatherConfig:
    name: str = "AccuWeather"
    url: str = "http://dataservice.accuweather.com/currentconditions/v1/"
    forecast_url: str = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/"
    cache_file: str  = "./caches/accuweather.json"
    cache_timeout_secs: int = 3600  # Default cache timeout in seconds

@dataclass
class AccuWeatherForecastConfig:
    name: str = "AccuWeather"
    url: str = "http://dataservice.accuweather.com/forecasts/v1/daily/5day"
    cache_file: str  = "./caches/accuweather_forecast.json"
    cache_timeout_secs: int = 3600  # Default cache timeout in seconds

@dataclass
class AccuWeatherLocationConfig:
    name: str = "AccuWeather Location"
    url: str = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
    cache_file: str  = "./caches/location.json"
    cache_timeout_secs: int = 3600 * 24  # Default cache timeout in seconds

class AccuWeatherApi(PMWebApi):
    """
    A wrapper for the AccuWeather API that uses PMWebApi.
    This is a convenience function to create an instance of PMWebApi with the AccuWeatherConfig.
    """
    def __init__(self, config: SafeNamespace):
        self.config = AccuWeatherConfig()
        super().__init__(self.config.url, self.config.cache_file, self.config.cache_timeout_secs)
        _debug(f"AccuWeatherApi initialized with params: {config}")
        self.params = AccuWeatherParams(**config.__dict__)
        self.location_key = None

    def _to_daily(self, r, f, d):        
        return {
            "dt": f.EpochDate,
            "summary": f.Day.IconPhrase,
            "temp": {
                "day": (f.Temperature.Minimum.Value + f.Temperature.Maximum.Value) / 2,
                "min": f.Temperature.Minimum.Value,
                "max": f.Temperature.Maximum.Value,
                "night": f.Temperature.Maximum.Value,
                "eve": f.Temperature.Maximum.Value,
                "morn": f.Temperature.Minimum.Value,
            },
            "feels_like": {
                "day": (f.Temperature.Minimum.Value + f.Temperature.Maximum.Value) / 2,
                "night": f.Temperature.Maximum.Value,
                "eve": f.Temperature.Maximum.Value,
                "morn": f.Temperature.Minimum.Value,
            },
            "pressure": d["pressure"],
            "humidity": d["humidity"],
            "dew_point": d["dew_point"],
            "wind_speed": d["wind_speed"],
            "wind_deg": d["wind_deg"],
            "wind_gust": d["wind_gust"],
            "weather": [PMWeatherSummary(id=1, main=f.Day.IconPhrase, description=f.Day.IconPhrase, icon=f"{f.Day.Icon}").__dict__],
            "clouds": r.CloudCover,
            "pop": 0.0,
            "rain": 0.0,
            "uvi": d["uvi"]
        }

    def get_weather_data(self, params = None) -> PMWeatherData:
        """
        Fetches weather data from the AccuWeather API.
        If params are provided, they will be used in the request.
        """
        self.get_location_data() ## get the location key if not already set
        self.get_forecast_data() ## get the forecast data if not already set
        params = {
            "_resource_id": self.location_key,
            "apikey": self.params.apikey,
            "details": True,
            "language": self.params.language,
        }
        response = self.get_json(params)
        if not response: return None
        r = SafeNamespace(**(response[0]))
        units = self.params.units.capitalize()
        c = {
            "dt": datetime.fromisoformat(r.LocalObservationDateTime).timestamp(),
            "temp":  r.Temperature[units].Value,
            "feels_like":  r.RealFeelTemperature[units].Value,
            "pressure":  r.Pressure[units].Value,
            "humidity":  r.RelativeHumidity,
            "dew_point":  r.DewPoint[units].Value,
            "uvi":  r.UVIndexFloat,
            "clouds":  r.CloudCover,
            "visibility":  r.Visibility[units].Value,
            "wind_speed":  r.Wind.Speed[units].Value,
            "wind_deg":  r.Wind.Direction.Degrees,
            "wind_gust":  r.WindGust.Speed[units].Value
        }
        f = [self._to_daily(r, f, c) for f in self.forecast_data.DailyForecasts if f.EpochDate >= r.EpochTime]
        w = {
            "lat": float(self.params.lat),
            "lon":  float(self.params.lon),
            "timezone": self.location_data.TimeZone.Name,
            "timezone_offset": self.location_data.TimeZone.GmtOffset * 3600,
            "current":  c,
            "daily":  f,
            "alerts": None
        }
        _debug(f"AccuWeatherApi response: {json_dumps(w)}")
        weather = PMWeatherData.from_dict(w)
        return weather

    def get_location_data(self) -> str:
        if self.location_key: return self.location_key
        config = AccuWeatherLocationConfig()
        location_api = PMWebApi(config.url, config.cache_file, config.cache_timeout_secs)
        location_data = location_api.get_json({
            "apikey": self.params.apikey,
            "q": f"{self.params.lat},{self.params.lon}",
            "details": "false",
            "toplevel": "false"
        })
        self.location_data = SafeNamespace(**location_data)
        self.location_key = location_data["Key"]
        _debug(f"AccuWeather location key: {self.location_key}")
        return self.location_key

    def get_forecast_data(self) -> str:
        config = AccuWeatherForecastConfig()
        forecast_api = PMWebApi(config.url, config.cache_file, config.cache_timeout_secs)
        forecast_data = forecast_api.get_json({
            "_resource_id": self.location_key,
            "apikey": self.params.apikey,
            "details": True,
            "language": self.params.language,
            "metric": self.params.units.lower() == "metric"
        })
        self.forecast_data = SafeNamespace(**forecast_data)
        _debug(f"AccuWeather forecast_data: {self.forecast_data}")
        return self.forecast_data