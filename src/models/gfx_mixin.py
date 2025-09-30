from dataclasses import dataclass

@dataclass
class GfxMixin:
    """Common graphics fields"""
    ## color
    color: str = "#fff"
    bg_color: str = "#000" 
    #text
    text_color: str = "#fff"
    text_bg_color: str = None
    wrap: str = "words"  # "chars", "words", or None
    halign: str = "center"  # "left", "center", "right"
    valign: str = "center"
    ## drawing
    line_width: int = 1

