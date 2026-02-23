from dataclasses import dataclass, field
from configs.pmdb_config import PmdbConfig
from configs.screen_config import ScreenConfig

@dataclass
class TuroConfig:
    database: str = ""
    refresh_time: str = "60s"