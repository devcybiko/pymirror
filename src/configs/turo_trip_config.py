from dataclasses import dataclass
from datetime import datetime

@dataclass
class TuroTripConfig:
    database: str = ""
    vehicle_nickname: str = ""
    refresh_time: str = "60s"
    nmonths: int = 3
    start_date: str = datetime.now().strftime("%Y-%m-%d")