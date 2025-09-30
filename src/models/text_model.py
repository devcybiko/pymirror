from dataclasses import dataclass
from models.pmmodel import PMModel
from models.font_mixin import FontMixin

@dataclass
class TextModel(PMModel, FontMixin):
    height: int = 16