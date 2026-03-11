from dataclasses import dataclass
from datetime import datetime

@dataclass
class TuroTripConfig:
    database_url: str 
    vehicle_nickname: str 
    refresh_time: str = "60s"
    nmonths: int = 3
    start_date: str = datetime.now().strftime("%Y-%m-%d")
    hide_months: bool = False
    hide_vehicle_name: bool = False