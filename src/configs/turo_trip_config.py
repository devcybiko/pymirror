from dataclasses import dataclass, field
from datetime import datetime
from configs.pmdb_config import PmdbConfig
from configs.screen_config import ScreenConfig

@dataclass
class TuroTripConfig:
    database: str = ""
    vehicle_nickname: str = ""
    refresh_time: str = "60s"
    nmonths: int = 3
    start_date: str = datetime.now().strftime("%Y-%m-%d")