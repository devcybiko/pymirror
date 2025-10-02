from dataclasses import dataclass, field
from configs.pmdb_config import PmdbConfig
from configs.screen_config import ScreenConfig

@dataclass
class PymirrorConfig:
    screen: ScreenConfig
    pmdb: PmdbConfig
    debug: bool = False
    secrets: str = ".secrets"
    force_render: bool = False
    positions: dict = field(default_factory=dict)
    modules: list = field(default_factory=list)
