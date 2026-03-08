from dataclasses import dataclass

@dataclass
class AnalogClockConfig:
    hour_hand: str = "#ff0000"
    minute_hand: str = "#00ff00" 
    second_hand: str = "#cc0"
