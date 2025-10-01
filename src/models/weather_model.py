from dataclasses import dataclass
from models.pmmodel import PMModel
from models.font_mixin import FontMixin

@dataclass
class WeatherModel(PMModel):
    refresh_minutes: str = "15"
    degrees: str = "°F"
    datetime_format: str = "%A, %I:%M:%S %p"
