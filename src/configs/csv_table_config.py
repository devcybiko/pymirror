from dataclasses import dataclass
from configs.mixins.font_mixin import FontMixin
from configs.mixins.text_mixin import TextMixin

@dataclass
class CsvTableConfig(TextMixin, FontMixin):
    fname: str = None
