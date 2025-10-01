from dataclasses import dataclass
from models.pmmodel import PMModel
from models.font_mixin import FontMixin

@dataclass
class SlideshowModel(PMModel):
    folder: str
    scale: str = "fill"
    valign: str = "center"
    halign: str = "center"
    interval_time: str = "60s"
    randomize: bool = True
    frame: str = None
