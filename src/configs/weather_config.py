from dataclasses import dataclass

@dataclass
class WeatherConfig:
    refresh_time: str = "15m"
    degrees: str = "°F"
    datetime_format: str = "%A, %I:%M:%S %p"
