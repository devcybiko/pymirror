from dataclasses import dataclass
from models.pmmodel import PMModel

@dataclass
class SlideshowModel:
    folder: str
    scale: str = "fill"
    valign: str = "center"
    halign: str = "center"
    interval_time: str = "60s"
    randomize: bool = True
    frame: str = None
    rect: str = None
