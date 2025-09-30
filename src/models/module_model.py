from dataclasses import dataclass
from models.pmmodel import PMModel

@dataclass
class ModuleModel(PMModel):
    ## moddef
    name: str = None
    position: str = "None"
    subscriptions: list[str] = None
    disabled: bool = False
    force_render: bool = False
    force_update: bool = False
    ## gfx
    color: str = "#fff"
    bg_color: str = None
    text_color: str = "#fff"
    text_bg_color: str = None
    ## font
    font_name: str = "DejaVuSans"
    font_size: int = 64
    font_baseline: bool = False
    font_y_offset: int = 0
