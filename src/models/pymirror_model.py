from dataclasses import dataclass, field
from models.pmdb_model import PmdbModel
from models.pmmodel import PMModel
from models.screen_model import ScreenModel

@dataclass
class PymirrorModel:
    screen: ScreenModel
    pmdb: PmdbModel
    debug: bool = False
    secrets: str = ".secrets"
    force_render: bool = False
    positions: dict = field(default_factory=dict)
    modules: list = field(default_factory=list)
