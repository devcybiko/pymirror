from dataclasses import dataclass
from models.pmmodel import PMModel

@dataclass
class OpenweathermapModel:
    appid: str
    lat: str
    lon: str
