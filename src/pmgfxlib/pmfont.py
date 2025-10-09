from dataclasses import dataclass
from typing import ClassVar, Optional
from PIL import ImageFont
from utils.utils import _height, _width
from pymirror.pmlogger import trace, _debug

@dataclass
class PMFont:
    ## Class variables
    FONT_LIST: ClassVar[Optional[list]] = None
    FONT_LIST_FNAME: ClassVar[str] = "./fontlist.txt"

    ## instance variables
    _name: str = "DejaVuSans"  # default font name
    _pitch: int = 64
    _antialias: bool = True
    _font: Optional[ImageFont.FreeTypeFont] = None
    _font_metrics: tuple = (0, 0, 0, 0)  # (offset, baseline, width, height)

    def __post_init__(self):
        if not PMFont.FONT_LIST:
            PMFont.FONT_LIST = []
            PMFont.FONT_LIST = self._read_fontlist()
        self.set_font(self._name, self._pitch)

    @property
    def name(self) -> str:
        return self._name

    @property
    def pitch(self) -> int:
        return self._pitch

    @property
    def height(self) -> int:
        return self._font_metrics[3]

    @property
    def width(self) -> int:
        return self._font_metrics[2]

    @property
    def offset(self) -> int:
        return self._font_metrics[0]

    @property
    def baseline(self) -> int:
        return self._font_metrics[1]
    
    @property
    def metrics(self) -> tuple:
        return self._font_metrics

    def _read_fontlist(self, font_list_fname: str = None) -> None:
        if PMFont.FONT_LIST: return
        if not font_list_fname:
            font_list_fname = PMFont.FONT_LIST_FNAME
        font_list = []
        with open(font_list_fname, "r") as f:
            fonts = f.read().splitlines()
            for font_path in fonts:
                _debug("Reading font list from", font_path)
                # split line at # discard the rest
                font_path = font_path.split("#")[0].strip()
                if not font_path:
                    continue  # skip empty lines
                # split after the : # discard the rest
                font_path = font_path.split(":")[0].strip()
                if not font_path:
                    continue  # skip empty lines
                font_list.append(font_path)
        return font_list

    def set_font(self, font_name: str, pitch: int = 64) -> bool:
        if not pitch:
            pitch = self._pitch
        if not font_name:
            font_name = self._name
        for font_path in PMFont.FONT_LIST:
            try:
                if font_name in font_path:
                    self._name = font_name
                    self._pitch = int(pitch)
                    self._font = ImageFont.truetype(font_path, size=self._pitch)
                    self._font_metrics = self._font.getbbox("M")
                    return True  # successfully set the font
            except Exception as e:
                _debug(f"Error setting font '{font_path}': {e}")
        return False

    def getbbox(self, text: str) -> tuple:
        """Get the bounding box of the text."""
        if not self._font:
            raise ValueError("Font not set. Call set_font() first.")
        return self._font.getbbox(text)

    def fit_text_chars(self, msg: str, rect: tuple) -> int:
        n = 0
        last_n = 0
        max = len(msg)
        while True:
            if n >= max: return n
            last_n = n
            width = self._font.getbbox(msg[:n])[2]  # Get width of the text
            if width > _width(rect):
                return last_n
            n += 1

    def fit_text_words(self, words: list[str], rect: tuple) -> int:
        n = 0
        last_n = 0
        max = len(words)
        while True:
            if n > max: return n
            test_words = words[:n]
            test_line = " ".join(test_words)
            width = self._font.getbbox(test_line)[2]  # Get width of the text
            if width >= _width(rect): return last_n
            last_n = n
            n += 1

    def text_split_words(self, s, rect: tuple) -> list[str]:
        words = s.split()
        n = 0
        end = len(words)
        lines = []
        while True:
            test_words = words[n:]
            l = self.fit_text_words(test_words, rect)
            if l == 0: break
            lines.append(" ".join(words[n:n+l]))
            n += l
            if n >= end: break
        return lines

    def text_split_chars(self, s, rect: tuple) -> list[str]:
        n = 0
        lines = []
        max = len(s)
        while True:
            if n >= max:
                break
            if s[n] == ' ':
                n += 1
                continue
            l = self.fit_text_chars(s[n:], rect)
            if l == 0:
                break
            lines.append(s[n:n+l])
            n += l
        return lines

    def text_no_split(self, s, rect: tuple) -> list[str]:
        return [s]  # No splitting, return the whole string as a single line

    def text_split(self, s, rect:tuple, split=None) -> list[str]:
        if s == None or not s.strip():
            s = ""
        split_fns = {
            "chars": self.text_split_chars,
            "words": self.text_split_words,
            "none": self.text_no_split
        }
        split_fn = split_fns.get(split or "none", self.text_no_split)
        results = []
        height = 0
        for s in s.splitlines():
            if height >= _height(rect):
                break
            s = s.strip()
            split_lines = split_fn(s, rect)
            results.extend(split_lines)
            height += self.height * len(split_lines)
        return results