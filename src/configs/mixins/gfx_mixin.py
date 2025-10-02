from dataclasses import dataclass

@dataclass
class GfxMixin:
    """Common graphics fields"""
    color: str = "#fff"
    bg_color: str = "#000" 
    line_width: int = 1

