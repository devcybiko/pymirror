from dataclasses import dataclass

@dataclass
class OpenweathermapConfig:
    appid: str
    lat: str
    lon: str
