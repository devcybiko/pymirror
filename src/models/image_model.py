from dataclasses import dataclass
from models.pmmodel import PMModel
from models.font_mixin import FontMixin

@dataclass
class ImageModel(PMModel):
    path: str
    scale: str = "fit"
