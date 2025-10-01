from dataclasses import dataclass
from models.mixins.font_mixin import FontMixin
from models.mixins.text_mixin import TextMixin

@dataclass
class TextModel(TextMixin, FontMixin):
    text: str = None
    height: int = 32