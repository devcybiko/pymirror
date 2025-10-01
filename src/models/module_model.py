from dataclasses import dataclass, field

from models.mixins.font_mixin import FontMixin
from models.mixins.gfx_mixin import GfxMixin
from models.mixins.text_mixin import TextMixin

@dataclass
class ModuleModel(GfxMixin, FontMixin, TextMixin):
    ## moddef
    clazz: str = field(default=None, metadata={"json_key": "class"})
    name: str = None
    position: str = "None"
    subscriptions: list[str] = None
    disabled: bool = False
    force_render: bool = False
    force_update: bool = False
