from dataclasses import dataclass

@dataclass
class PMConstants:
    font_name: str = "DejaVuSans"
    font_size: int = 64
    color: str = "#fff"
    bg_color: str = None
    text_color: str = "#000"
    text_bg_color: str = "#fff"
    halign: str = "center"  # "left", "center", "right"
    valign: str = "center"  # "top", "center", "bottom"
    wrap: str = "words"  # "chars", "words", or None
