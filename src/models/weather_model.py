from dataclasses import dataclass
from models.pmmodel import PMModel

@dataclass
class WeatherModel:
    refresh_time: str = "15m"
    degrees: str = "°F"
    datetime_format: str = "%A, %I:%M:%S %p"
