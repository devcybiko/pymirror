from dataclasses import dataclass
from configs.mixins.font_mixin import FontMixin
from configs.mixins.text_mixin import TextMixin

@dataclass
class TextConfig(TextMixin, FontMixin):
    text: str = None
    height: int = 32