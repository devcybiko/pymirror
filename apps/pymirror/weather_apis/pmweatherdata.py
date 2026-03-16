##
## Generic Weather API Data Classes
## These classes are used to represent weather data from various APIs.
## Loosely based on OpenWeatherMap API str = Noneucture.
##

from dataclasses import dataclass, fields
from typing import get_args, get_origin

class PMDataClassBase:
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dict, ignoring unexpected keys and handling nested objects"""
        if data is None:
            return None
            
        field_names = {f.name: f for f in fields(cls)}
        kwargs = {}
        
        for field_name, field_info in field_names.items():
            if field_name in data:
                value = data[field_name]
                field_type = field_info.type
                
                # Handle nested dataclasses
                if hasattr(field_type, 'from_dict'):
                    kwargs[field_name] = field_type.from_dict(value)
                # Handle lists of dataclasses
                elif get_origin(field_type) is list:
                    list_type = get_args(field_type)[0]
                    if hasattr(list_type, 'from_dict') and isinstance(value, list):
                        kwargs[field_name] = [list_type.from_dict(item) for item in value]
                    else:
                        kwargs[field_name] = value
                else:
                    kwargs[field_name] = value
        
        return cls(**kwargs)

@dataclass
class PMWeatherAlert(PMDataClassBase):
    sender_name: str = None
    event: str = None
    start: int = None
    end: int = None
    description: str = None
    tags: list[str] = None
  
@dataclass
class PMWeatherSummary(PMDataClassBase):
  id: int = None
  main: str = None
  description: str = None
  icon: str = None

@dataclass
class PMWeatherFeelsLike(PMDataClassBase):
    day:  float = None
    night:  float = None
    eve:  float = None
    morn:  float = None

@dataclass
class PMWeatherTemps(PMDataClassBase):
    day:  float = None
    min:  float = None
    max:  float = None
    night:  float = None
    eve:  float = None
    morn:  float = None

@dataclass
class PMWeatherDaily(PMDataClassBase):
      dt: int = None
      summary: str = None
      temp: PMWeatherTemps = None
      feels_like: PMWeatherFeelsLike = None
      pressure:  float = None
      humidity:  float = None
      dew_point:  float = None
      wind_speed:  float = None
      wind_deg:  float = None
      wind_gust:  float = None
      weather: list[PMWeatherSummary] = None
      clouds:  float = None
      pop:  float = None
      rain:  float = None
      uvi:  float = None

@dataclass
class PMWeatherCurrent(PMDataClassBase):
  dt: int = None
  temp:  float = None
  feels_like:  float = None
  pressure:  float = None
  humidity:  float = None
  dew_point:  float = None
  uvi:  float = None
  clouds:  float = None
  visibility:  float = None
  wind_speed:  float = None
  wind_deg:  float = None
  wind_gust:  float = None

@dataclass
class PMWeatherData(PMDataClassBase):
    lat:  float = None
    lon:  float = None
    timezone: str = None
    timezone_offset: int = None
    current: PMWeatherCurrent = None
    daily: list[PMWeatherDaily] = None
    alerts: list[PMWeatherAlert] = None