import time
from pymirror.utils.utils import _sub, _add, _norm, _scale, color_from_tuple, color_to_tuple, tocolor

##
## GLS - defunct... maybe remove?
## This is a class to handle color fading in PMGfx.
##
class PMFader:
    """Class to handle color fading in PMGfx."""
    def __init__(self, from_color: str, to_color: str, secs: float):
        self.from_color = tocolor(from_color)
        self.from_color_tuple = color_to_tuple(self.from_color)
        self.to_color = tocolor(to_color)
        self.to_color_tuple = color_to_tuple(self.to_color)
        self.diff_color_tuple = _sub(self.to_color_tuple, self.from_color_tuple)
        self.to_color_norm = _norm(self.to_color_tuple)
        self.done = False
        self.start_time = 0
        self.secs = secs

    def start(self) -> int:
        """Start the fading process by returning the initial color."""
        self.done = False
        self.start_time = time.time()
        return self.from_color

    def next(self, current_color: int) -> int:
        if self.done: return current_color
        now = time.time()
        delta_time = now - self.start_time
        # print(f"Delta time: {delta_time} seconds")
        percent_fade = delta_time / self.secs
        diff = _scale(self.diff_color_tuple, percent_fade)
        t = _add(self.from_color_tuple, diff)
        norm_t = _norm(t)
        error = abs(norm_t - self.to_color_norm)
        if error <= .1 or any(x < 0.0 for x in t) or any(x > 1.0 for x in t):
            self.done = True
            new_color = self.to_color
        else:
            new_color = color_from_tuple(t)
        # print(f"Fading color: {t} error: {error}")
        return new_color

    def is_done(self) -> bool:
        return self.done
