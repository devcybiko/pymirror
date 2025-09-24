import os
from dataclasses import dataclass
from PIL import Image
from pmgfxlib import PMBitmap, PMGfx
from pymirror.utils.utils import from_dict
from .pmlogger import _debug

@from_dict
@dataclass
class PMScreenConfig:
        width: int = 1920
        height: int = 1080
        rotate: int = 0  # Rotation angle in degrees
        color: str = "#fff"  # default color
        bg_color: str = "#000"  # default background color
        text_color: str = color
        text_bg_color: str = None
        line_width: int = 1
        font_name: str = "Roboto-Regular"
        font_size: int = 64
        output_file: str = None
        frame_buffer: str = None # Path to framebuffer device

class PMScreen:
    def __init__(self, _config):
        self._config = _config
        ## by convention the config for an object is _classname
        self._screen = _screen = PMScreenConfig.from_dict(_config.__dict__)
        if self._screen.rotate:
            if self._screen.rotate not in [0, 90, 180, 270]:
                raise ValueError(f"Invalid rotation angle: {self._screen.rotate}. Must be one of 0, 90, 180, or 270 degrees.")
            if self._screen.rotate == 90 or self._screen.rotate == 270:
                self._screen.width, self._screen.height = self._screen.height, self._screen.width
        # Initialize the bitmap with the screen dimensions
        self.bitmap = PMBitmap(_screen.width, _screen.height)
        gfx = self.bitmap.gfx
        gfx.rect = (0, 0, _screen.width-1, _screen.height-1)
        gfx.color = _screen.color or gfx.color
        gfx.bg_color = _screen.bg_color or gfx.bg_color
        gfx.text_color = _screen.text_color or gfx.text_color
        gfx.text_bg_color = _screen.text_bg_color or gfx.text_bg_color
        gfx.line_width = _screen.line_width or gfx.line_width
        gfx.set_font(self._screen.font_name, self._screen.font_size)

        self._hard_clear()

    def _hard_clear(self):
        """Clear the framebuffer by writing zeros to it."""
        if self._screen.frame_buffer:
            # Open the framebuffer device and write zeros to it
            with open(self._screen.frame_buffer, "wb") as f:
                f.write(b'\x00' * (1920 * 1080 * 2))  # Assuming RGB565 format, 2 bytes per pixel

    def _write_framebuffer(self, img: Image.Image) -> None:
        """Write the image to the framebuffer."""
        # self._screen.frame_buffer = "./fb0.jpg"
        if self._screen.frame_buffer:
            _debug(f"Writing to framebuffer: {self._screen.frame_buffer}")
            from clib import rgba_to_rgb16
            _debug(f"Image size: {img.size}, mode: {img.mode}")
            if self._screen.rotate:
                img = img.rotate(self._screen.rotate, expand=True)
            raw = img.tobytes("raw")
            _debug(f"Raw image size: {len(raw)} bytes")
            # Convert the image to RGB565 format
            rgb565 = rgba_to_rgb16(raw, img.width, img.height)
            _debug(f"Converted to RGB565 size: {len(rgb565)} bytes")
            with open(self._screen.frame_buffer, "wb") as f:
                _debug(f"Saving RGB565 image to {self._screen.frame_buffer}")
                f.write(rgb565)
            _debug("Framebuffer write complete")
            rgb565 = rgba_to_rgb16(raw, img.width, img.height)
            _debug(f"Converted to RGB565 size: {len(rgb565)} bytes")
            with open(self._screen.frame_buffer, "wb") as f:
                _debug(f"Saving RGB565 image to {self._screen.frame_buffer}")
                f.write(rgb565)
            _debug("Framebuffer write complete")

    def _atomic_write(self, img: Image.Image) -> None:
        if self._screen.output_file:
            self.bitmap._img.convert("RGB").save(self._screen.output_file+".tmp", "JPEG")
            os.rename(self._screen.output_file+".tmp", self._screen.output_file)

    def flush(self) -> None:
        img = self.bitmap._img
        self._write_framebuffer(img)
        self._atomic_write(img)
