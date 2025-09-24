from dataclasses import dataclass
from logging import config
from pymirror.pmwebapi import PMWebApi
from pymirror.utils.utils import SafeNamespace
from .pmweatherdata import PMWeatherAlert, PMWeatherCurrent, PMWeatherDaily, PMWeatherData, PMWeatherSummary

@dataclass 
class OpenWeatherMapParams:
    appid: str = ""
    lat: str = "37.5050"
    lon: str = "-77.6491"
    exclude: str = "minutely,hourly"
    units: str = "imperial"
    lang: str = "english"

@dataclass
class OpenWeatherMapConfig:
    name: str = "OpenWeatherMap"
    url: str = "https://api.openweathermap.org/data/3.0/onecall"
    cache_file: str  = "./caches/weather.json"
    cache_timeout_secs: int = 3600  # Default cache timeout in seconds

def _paragraph_fix(text: str) -> str:
    results = []
    paragraphs = text.split("\n\n")
    for paragraph in paragraphs:
        lines = paragraph.split("\n")
        paragraph = " ".join(line.strip() for line in lines)
        results.append(paragraph)
    return "\n\n".join(results)

class OpenWeatherMapApi(PMWebApi):
    """
    A wrapper for the OpenWeatherMap API that uses PMWebApi.
    This is a convenience function to create an instance of PMWebApi with the OpenWeatherMapConfig.
    """
    def __init__(self, config: SafeNamespace):
        self.config = OpenWeatherMapConfig()
        super().__init__(self.config.url, self.config.cache_timeout_secs, self.config.cache_file)
        self.params = OpenWeatherMapParams(**config.__dict__)
    
    def get_weather_data(self, params = None) -> PMWeatherData:
        """
        Fetches weather data from the OpenWeatherMap API.
        If params are provided, they will be used in the request.
        """
        if not params:
            params = self.params.__dict__
        self._httpx.params=params
        response = self.fetch_json(blocking=False)
        if not response: return None
        weather = PMWeatherData.from_dict(response)
        if weather.alerts:
            for alert in weather.alerts:
                if alert.description:
                    alert.description = _paragraph_fix(alert.description)
        return weather
