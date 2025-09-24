from dataclasses import dataclass, fields

from pymirror.pmrect import PMRect
from pymirror.utils.utils import _NONE_PROXY, from_dict, non_null
from .pmfont import PMFont
from .pmutils import to_color

@dataclass
class PMGfx:
    ## instance variables
    _color: tuple = (255, 255, 255) 
    _bg_color: tuple = (0, 0, 0) 
    _text_color: tuple = (255, 255, 255)
    _text_bg_color: tuple = None  
    line_width: int = 1
    font_name: str = "DejaVuSans"
    font_size: int = 64
    font: PMFont = None
    wrap: str = "words"  # "chars", "words", or None
    halign: str = "center"  # "left", "center", "right"
    valign: str = "center"

    @classmethod
    def from_dict(cls, config: dict, _gfx: "PMGfx" = _NONE_PROXY) -> "PMGfx":
        gfx = cls()
        gfx.line_width = non_null(config.get('line_width'), _gfx.line_width, 1)
        gfx.font_name = non_null(config.get('font_name'), _gfx.font_name, "DejaVuSans")
        gfx.font_size = non_null(config.get('font_size'), _gfx.font_size, 64)
        gfx.set_font(gfx.font_name, gfx.font_size)
        gfx.wrap = non_null(config.get('wrap'), _gfx.wrap, "words")
        gfx.halign = non_null(config.get('halign'), _gfx.halign, "center")
        gfx.valign = non_null(config.get('valign'), _gfx.valign, "center")
        gfx.color = non_null(config.get('color'), _gfx.color, (255, 255, 255))
        gfx.bg_color = non_null(config.get('bg_color'), _gfx.bg_color, (0, 0, 0))
        gfx.text_color = non_null(config.get('text_color'), _gfx.text_color, (255, 255, 255))
        gfx.text_bg_color = non_null(config.get('text_bg_color'), _gfx.text_bg_color, None)
        return gfx

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