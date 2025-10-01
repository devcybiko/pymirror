from dataclasses import dataclass
from models.mixins.font_mixin import FontMixin
from models.mixins.gfx_mixin import GfxMixin
from models.mixins.text_mixin import TextMixin


@dataclass
class ScreenModel(FontMixin, GfxMixin, TextMixin):
    ## screen
    width: int = 1920
    height: int = 1080
    rotate: int = 0  # Rotation angle in degrees
    output_file: str = None
    frame_buffer: str = None # Path to framebuffer device