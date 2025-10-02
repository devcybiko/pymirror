##
## This is the PyMirror implementation-independent bitmap class.
## This implementation uses the Pillow library for image manipulation.
## It's intended that other bitmap implementations can be created
## for different graphics libraries.
## But the interface should remain the same.
##
## PMBitmap is the lowest level graphcics class in PyMirror.
##

import copy
from dataclasses import dataclass
from email.mime import image
from PIL import Image, ImageDraw, ImageColor

from pymirror.pmrect import PMRect
from pymirror.pmlogger import _trace, _debug
from pymirror.utils.utils import SafeNamespace, non_null
from .pmgfx import PMGfx

CENTER = 0
BOTTOM = 1
TOP = 2
LEFT = 1
RIGHT = 2


class PMBitmap:
    def __init__(self, width: int = None, height: int = None, config: dataclass = None):
        self.gfx = PMGfx().merge(config)
        self._gfx_stack = []
        self._rect = PMRect(0, 0, non_null(width, 1) - 1, non_null(height, 1) - 1)
        self._img = Image.new("RGBA", (self._rect.width, self._rect.height), 0)
        self._draw = ImageDraw.Draw(self._img)

    @property
    def rect(self) -> PMRect:
        return self._rect

    @rect.setter
    def rect(self, value: PMRect) -> None:
        if isinstance(value, PMRect):
            self._rect = value
        elif isinstance(value, tuple) and len(value) == 4:
            self._rect = PMRect(*value)
        else:
            raise TypeError("rect must be an instance of PMRect")

    @property
    def x0(self):
        return self.rect[0]

    @property
    def y0(self):
        return self.rect[1]

    @property
    def x1(self):
        return self.rect[2]

    @property
    def y1(self):
        return self.rect[3]

    @property
    def width(self):
        return self._rect.width

    @property
    def height(self):
        return self._rect.height

    @width.setter
    def width(self, value: int):
        self._rect.width = value

    @height.setter
    def height(self, value: int):
        self._rect.height = value

    def load(self, photo_path, width=None, height=None, scale=None) -> "PMBitmap":
        _trace("...Loading bitmap from", photo_path)
        self._img = Image.open(photo_path).convert(
            "RGBA"
        )  # Ensure the image is in RGBA format
        self._draw = ImageDraw.Draw(self._img)
        self.gfx.rect = (0, 0, self._img.width - 1, self._img.height - 1)
        self.scale(
            width or self._img.width, height or self._img.height, scale or "stretch"
        )
        return self

    def gfx_push(self, gfx: PMGfx = None) -> PMGfx:
        """Push the current graphics state onto the stack."""
        # Save the current graphics state
        self._gfx_stack.append(self.gfx)
        # If gfx is provided, use it; otherwise, keep the current state
        if gfx == None:
            self.gfx = copy.copy(self.gfx)
        else:
            self.gfx = copy.copy(gfx)
        # Return the current graphics state
        # you can modify this gfx object and it will not affect the previous state
        return self.gfx

    def gfx_pop(self) -> PMGfx:
        """Pop the last graphics state from the stack."""
        self.gfx = self._gfx_stack.pop()
        return self.gfx

    def clear(self) -> None:
        self._draw.rectangle(
            (0, 0, self._img.width, self._img.height), fill=self.gfx.bg_color
        )

    def line(self, rect: tuple):
        self._draw.line(rect, fill=self.gfx.color, width=self.gfx.line_width)

    def ellipse(self, rect: tuple, fill=-1) -> None:
        if fill == -1:
            # Use the gfx.background color if specified
            self._draw.ellipse(
                rect,
                outline=self.gfx.color,
                width=self.gfx.line_width,
                fill=self.gfx.bg_color,
            )
        else:
            # Use the specified fill color
            self._draw.ellipse(
                rect, outline=self.gfx.color, width=self.gfx.line_width, fill=fill
            )

    def circle(self, x0: int, y0: int, r: int, fill=-1) -> None:
        bbox = (x0 - r, y0 - r, x0 + r, y0 + r)
        self.ellipse(bbox, fill=fill)

    def rectangle(self, rect: tuple, fill=-1) -> None:
        if fill == -1:
            # Use the gfx.background color if specified
            self._draw.rectangle(
                rect,
                outline=self.gfx.color,
                width=self.gfx.line_width,
                fill=self.gfx.bg_color,
            )
        else:
            # Use the specified fill color
            self._draw.rectangle(
                rect, outline=self.gfx.color, width=self.gfx.line_width, fill=fill
            )

    def text(self, msg: str, x0: int, y0: int, fill=-1) -> None:
        if fill == -1:
            # Use the gfx.background color if specified
            self._draw.text(
                (x0, y0+self.gfx.font_y_offset), msg, font=self.gfx.font._font, fill=self.gfx._text_color
            )
        else:
            # Use the specified fill color
            self._draw.text((x0, y0+self.gfx.font_y_offset), msg, font=self.gfx.font._font, fill=fill)

    def calculate_text_box(self, lines: str) -> tuple[str, tuple[int, int]]:
        """Calculate the size of the text."""
        width = 0
        height = 0
        results = []
        (x_min, baseline, line_width, font_height) = self.gfx.font.getbbox("M")
        for multi_line in lines:
            multi_lines = multi_line.split("\n")
            for line in multi_lines:
                results.append(line)
                (x_min, baseline, line_width, _font_height) = self.gfx.font.getbbox(line)
                width = max(width, line_width)
                height += font_height
        return results, (width, height)

    def text_box(
        self,
        rect,
        lines: str | list[str],
        valign: str = "center",
        halign: str = "center",
        clip: bool = False,
        use_baseline: bool = None
    ) -> None:
        clip = bool(clip) ## make sure it's zero or one
        if use_baseline == None:
            use_baseline =  self.gfx.font_baseline
        # use_baseline = bool(use_baseline) ## move the text down to shift descenders
        ## renders text in the entire bitmap area
        ## if you want a cliprect, create a PMBitmap with the cliprect size
        ## then render it and paste it into the parent PMBitmap
        rect = PMRect(*rect)  # Ensure rect is a PMRect object
        if lines == None:
            return
        if isinstance(lines, str):
            lines = [lines]
        valign = {"center": CENTER, "top": TOP, "bottom": BOTTOM}[valign or "center"]
        halign = {"center": CENTER, "left": LEFT, "right": RIGHT}[halign or "center"]
        x0, y0, x1, y1 = rect
        if self.gfx._text_bg_color:
            self._draw.rectangle(rect, fill=self.gfx._text_bg_color)
        gfx = self.gfx
        font = self.gfx.font
        (x_min, baseline, width, font_height) = font.getbbox("M")
        baseline *= (not use_baseline) ## sets baseline to zero if use_baseline is False
        lines, (text_width, text_height) = self.calculate_text_box(lines)
        if valign == CENTER:
            dy = rect.height - text_height
            text_y0 = y0 + int(dy / 2)
        elif valign == TOP:
            text_y0 = y0
        elif valign == BOTTOM:
            text_y0 = y1 - text_height
        else:
            _debug(
                f"Invalid valign '{type(valign), valign}' in text_box, using 'center' instead."
            )

        for multi_line in lines:
            multi_lines = multi_line.split("\n")
            for line in multi_lines:
                if text_y0 + font_height * clip > y1:
                    break
                (_x_min, _baseline, width, _font_height) = font.getbbox(line)
                if halign == CENTER:
                    text_x0 = x0 + int((rect.width - width) / 2)
                elif halign == LEFT:
                    text_x0 = x0
                elif halign == RIGHT:
                    text_x0 = x0 + int(rect.width - width)
                else:
                    _debug(
                        f"Invalid halign '{type(halign), halign}' in text_box, using 'center' instead."
                    )
                self._draw.text(
                    (text_x0, text_y0 - baseline + self.gfx.font_y_offset),
                    line,
                    fill=(gfx._text_color),
                    font=gfx.font._font,
                )
                text_y0 += font_height

    def paste(self, src: "PMBitmap", x0=None, y0=None, mask: "PMBitmap" = None) -> None:
        if x0 == None:
            x0 = src.gfx.x0
        if y0 == None:
            y0 = src.gfx.y0
        self._img.paste(src._img, (x0, y0), mask and mask._img)

    def scale_to_fit(self, target_width, target_height):
        """Scale image to fit within bounds, maintaining aspect ratio"""
        original_width, original_height = self._img.size

        # Calculate scale factor (use the smaller ratio)
        scale_x = target_width / original_width
        scale_y = target_height / original_height
        scale = min(scale_x, scale_y)  # Smaller ratio ensures it fits

        # Calculate new dimensions
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        _trace("GLS - CHECK THIS")
        if new_width < 0:
            new_width = 1
        if new_height < 0:
            new_height = 1
        self._img = self._img.resize((new_width, new_height), Image.LANCZOS)

    def scale_to_fill(self, target_width, target_height):
        """Scale image to fill entire area, cropping excess"""
        original_width, original_height = self._img.size

        # Calculate scale factor (use the larger ratio)
        scale_x = target_width / original_width
        scale_y = target_height / original_height
        scale = max(scale_x, scale_y)  # Larger ratio ensures it fills

        # Scale the image
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        new_image = self._img.resize((new_width, new_height), Image.LANCZOS)

        # Center crop to target size
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        self._img = new_image.crop((left, top, right, bottom))

    def scale(self, width=None, height=None, scale=None):
        if width is not None and height is not None:
            if scale == "fit":
                _debug(f"Scaling image to fit within {width}x{height}")
                self.scale_to_fit(width, height)
            elif scale == "fill":
                _debug(f"Scaling image to fill {width}x{height}")
                self.scale_to_fill(width, height)
            elif scale == "stretch":
                # Default to resizing without aspect ratio preservation
                _debug(f"...Stretching image to {width}x{height}")
                self._img = self._img.resize((width, height), Image.LANCZOS)
            self.rect = (
                self.x0,
                self.y0,
                self.x0 + width,
                self.y0 + height,
            )
