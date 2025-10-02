from dataclasses import dataclass

@dataclass
class FontMixin:
    """Common font fields"""
    font_name: str = "DejaVuSans"
    font_size: int = 64
    font_baseline: bool = True
    font_y_offset: int = 0
