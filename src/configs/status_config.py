from dataclasses import dataclass

@dataclass
class StatusConfig:
    valign: str = "bottom"
    halign: str = "center"
    interval_time: str = "10s"
    time_format: str = "9/1 0:00 pm"

