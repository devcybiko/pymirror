from dataclasses import dataclass
from logging import config
from pmdb.pmdb import PMDb
from pymirror.pmwebapi import PMWebApi
from utils.utils import SafeNamespace, json_dumps, json_loads, pprint, to_dict, to_munch
from tasks.web_api_task import WebApiTable
from .pmweatherdata import PMWeatherAlert, PMWeatherCurrent, PMWeatherDaily, PMWeatherData, PMWeatherSummary
from pymirror.pmlogger import _debug

def _paragraph_fix(text: str) -> str:
    results = []
    paragraphs = text.split("\n\n")
    for paragraph in paragraphs:
        lines = paragraph.split("\n")
        paragraph = " ".join(line.strip() for line in lines)
        results.append(paragraph)
    return "\n\n".join(results)

class OpenWeatherMapApi:
    """
    A wrapper for the OpenWeatherMap API that uses PMWebApi.
    This is a convenience function to create an instance of PMWebApi with the OpenWeatherMapConfig.
    """
    def __init__(self, pmdb: PMDb, name: str):
        self.pmdb = pmdb
        self.name = name
        self.text = ""
        self.last_text = None

    def get_weather_data(self) -> PMWeatherData:
        """
        Fetches weather data from the OpenWeatherMap API.
        If params are provided, they will be used in the request.
        """
        _record = self.pmdb.get_where(WebApiTable, WebApiTable.name == self.name)
        record = to_munch(to_dict(_record))
        self.text = record.result_text
        if not self.text:
            _debug("... db.get_where() returns None")
            return
        if self.last_text == self.text:
            _debug("... db.get_where() returns same value")
            return
        weather_dict = json_loads(self.text)
        weather = PMWeatherData.from_dict(weather_dict)
        if weather.alerts:
            for alert in weather.alerts:
                if alert.description:
                    alert.description = _paragraph_fix(alert.description)
        return weather

if __name__ == "__main__":
    pmdb = PMDb({"url":"sqlite:///pymirror.db"})
    openweathermap = OpenWeatherMapApi(pmdb, "openweather")
    weather_data = openweathermap.get_weather_data()
    pprint(weather_data)
