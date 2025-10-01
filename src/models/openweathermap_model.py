from dataclasses import dataclass
from models.pmmodel import PMModel
from models.font_mixin import FontMixin

@dataclass
class OpenweathermapModel(PMModel):
    appid: str
    lat: str
    lon: str
