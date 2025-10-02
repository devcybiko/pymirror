from dataclasses import dataclass, fields

from configs.fonts_config import FontsConfig
from configs.mixins.font_mixin import FontMixin
from configs.mixins.gfx_mixin import GfxMixin
from configs.mixins.text_mixin import TextMixin
from pymirror.pmrect import PMRect
from pymirror.utils.utils import _NONE_PROXY, from_dict, non_null
from .pmfont import PMFont
from .pmutils import to_color

@dataclass
class PMGfx(GfxMixin, TextMixin, FontMixin):
    ## instance variables
    _color: tuple = (255, 255, 255) 
    _bg_color: tuple = (0, 0, 0) 
    _text_color: tuple = (255, 255, 255)
    _text_bg_color: tuple = None  
    font: PMFont = None
    
    def merge(self, config: dataclass) -> "PMGfx":
        if isinstance(config, TextMixin):
            self.text_color = non_null(config.text_color, self.text_color, (255, 255, 255))
            self.text_bg_color = non_null(config.text_bg_color, self.text_bg_color, None)
            self.wrap = non_null(config.wrap, self.wrap, "words")
            self.halign = non_null(config.halign, self.halign, "center")
            self.valign = non_null(config.valign, self.valign, "center")
            self.clip = non_null(config.clip, self.clip, False)
            self.hscroll = non_null(config.hscroll, self.hscroll, False)

        if isinstance(config, GfxMixin):
            self.line_width = non_null(config.line_width, self.line_width, 1)
            self.color = non_null(config.color, self.color, (255, 255, 255))
            self.bg_color = non_null(config.bg_color, self.bg_color, (0, 0, 0))

        if isinstance(config, FontMixin):
            self.font_name = non_null(config.font_name, self.font_name, "DejaVuSans")
            self.font_size = non_null(config.font_size, self.font_size, 64)
            self.font_baseline = non_null(config.font_baseline, self.font_baseline, False)
            self.font_y_offset = non_null(config.font_y_offset, self.font_y_offset, 0)
            self.set_font( self.font_name,  self.font_size)

        return self

    def set_font(self, name: str, size: int) -> None:
        """Set the font for the graphics context."""
        self.font_name = name
        self.font_size = size
        self.font = PMFont(name, size)
    
    @property
    def color(self) -> tuple[int, int, int]:
        return self._color

    @color.setter
    def color(self, value: str | tuple[int, int, int]) -> None:
        if isinstance(value, str):
            self._color = to_color(value)
        else:
            self._color = value

    @property
    def bg_color(self) -> tuple[int, int, int]:
        return self._bg_color

    @bg_color.setter
    def bg_color(self, value: str | tuple[int, int, int]) -> None:
        if isinstance(value, str):
            self._bg_color = to_color(value)
        else:
            self._bg_color = value

    @property
    def text_color(self) -> tuple[int, int, int]:
        return self._text_color

    @text_color.setter
    def text_color(self, value: str | tuple[int, int, int]) -> None:
        if isinstance(value, str):
            self._text_color = to_color(value)
        else:
            self._text_color = value

    @property
    def text_bg_color(self) -> tuple[int, int, int]:
        return self._text_bg_color

    @text_bg_color.setter
    def text_bg_color(self, value: str | tuple[int, int, int]) -> None:
        if isinstance(value, str):
            self._text_bg_color = to_color(value)
        else:
            self._text_bg_color = value