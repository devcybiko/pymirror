from dataclasses import dataclass

@dataclass
class ImageConfig:
    path: str
    scale: str = "fit"
