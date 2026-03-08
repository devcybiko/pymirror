def _height(rect: tuple) -> int:
    return rect[3] - rect[1]


def _width(rect: tuple) -> int:
    return rect[2] - rect[0]


def _str_to_rect(rect: str) -> tuple:
    """Convert a rectangle string to a tuple of floats."""
    if not rect:
        return (0.0, 0.0, 1.0, 1.0)
    try:
        return tuple(float(x) for x in rect.split(","))
    except ValueError as e:
        raise ValueError(f"Invalid rectangle format: {rect}") from e

