from dataclasses import dataclass
from models.pmmodel import PMModel

@dataclass
class AnalogClockModel:
    hour_hand: str = "#ff0000"
    minute_hand: str = "#00ff00" 
    second_hand: str = "#cc0"
