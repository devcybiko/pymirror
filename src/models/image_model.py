from dataclasses import dataclass
from models.pmmodel import PMModel

@dataclass
class ImageModel:
    path: str
    scale: str = "fit"
