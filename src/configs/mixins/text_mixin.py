from dataclasses import dataclass

@dataclass
class TextMixin:
    text_color: str = "#fff"
    text_bg_color: str = None
    wrap: str = "words"  # "chars", "words", or None
    halign: str = "center"  # "left", "center", "right"
    valign: str = "center"
    clip: bool = False
    hscroll: bool = False
