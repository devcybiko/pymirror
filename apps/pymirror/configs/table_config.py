from dataclasses import dataclass
from configs.mixins.font_mixin import FontMixin
from configs.mixins.text_mixin import TextMixin

@dataclass
class TableConfig(TextMixin, FontMixin):
    has_header: bool = False
    rows: int = None
    cols: int = None
    height: int = None
    width: int = None
    row_height: int = None
    col_width: int = None
    reversed: bool = False