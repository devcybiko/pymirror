from dataclasses import dataclass, field
from configs.screen_config import ScreenConfig
from dataclasses import dataclass
from configs.pmdb_config import PmdbConfig

@dataclass
class PymirrorConfig:
    screen: ScreenConfig
    pmdb: PmdbConfig = None
    debug: bool = False
    secrets: str = ".secrets"
    force_render: bool = False
    positions: dict = field(default_factory=dict)
    tiles: list = field(default_factory=list)
    imports: list = field(default_factory=list)
