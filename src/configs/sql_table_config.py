from dataclasses import dataclass
from configs.mixins.font_mixin import FontMixin
from configs.mixins.text_mixin import TextMixin

@dataclass
class SqlTableConfig(TextMixin, FontMixin):
    sql: str = None
    database_url: str = None
