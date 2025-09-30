from dataclasses import dataclass
from models.font_mixin import FontMixin
from models.gfx_mixin import GfxMixin
from models.pmmodel import PMModel


@dataclass
class ScreenModel(PMModel, FontMixin, GfxMixin):
    ## screen
    width: int = 1920
    height: int = 1080
    rotate: int = 0  # Rotation angle in degrees
    output_file: str = None
    frame_buffer: str = None # Path to framebuffer device