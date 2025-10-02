from dataclasses import dataclass

@dataclass
class SlideshowConfig:
    folder: str
    scale: str = "fill"
    valign: str = "center"
    halign: str = "center"
    interval_time: str = "60s"
    randomize: bool = True
    frame: str = None
    rect: str = None
