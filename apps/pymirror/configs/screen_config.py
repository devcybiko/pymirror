from dataclasses import dataclass
from configs.mixins.font_mixin import FontMixin
from configs.mixins.gfx_mixin import GfxMixin
from configs.mixins.text_mixin import TextMixin


@dataclass
class ScreenConfig(FontMixin, GfxMixin, TextMixin):
    ## screen
    width: int = 1920
    height: int = 1080
    rotate: int = 0  # Rotation angle in degrees
    output_file: str = None
    frame_buffer: str = None # Path to framebuffer device