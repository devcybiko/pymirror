from dataclasses import dataclass, field

from configs.mixins.font_mixin import FontMixin
from configs.mixins.gfx_mixin import GfxMixin
from configs.mixins.text_mixin import TextMixin

@dataclass
class ModuleConfig(GfxMixin, FontMixin, TextMixin):
    ## moddef
    clazz: str = field(default=None, metadata={"json_key": "class"})
    name: str = None
    position: str = "None"
    subscriptions: list[str] = None
    disabled: bool = False
    force_render: bool = False
    force_update: bool = False
