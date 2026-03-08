from PIL import ImageColor

def to_color(color):
    """Convert a color string to an RGB tuple."""
    if isinstance(color, str):
        return ImageColor.getrgb(color)
    elif isinstance(color, tuple) and len(color) == 3:
        return color
    else:
        raise ValueError(f"Invalid color format: {color}")