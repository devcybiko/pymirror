
from attr import dataclass


@dataclass
class NullParent:
    x0: int = None
    y0: int = None
    x1: int = None
    y1: int = None
    width: int = None
    height: int = None

class PMRect:
    def __init__(self, X0: float, Y0: float, X1: float, Y1: float, parent=None):
        self._coords = [X0, Y0, X1, Y1]
        self.parent = parent or NullParent()

    def __iter__(self):
        return iter(self._coords)

    def __getitem__(self, index):
        return self._coords[index]

    def __setitem__(self, index, value):
        self._coords[index] = value

    def __len__(self):
        return 4

    def __tuple__(self):
        return tuple(self._coords)

    def _scale(self, value: float, max: (float | None) = None) -> int:
        if max is not None:
            result = int(value * max)
            return result
        return int(value)

    def _is_percentage(self, value: float) -> bool:
        if type(value) is float:
            is_percentage = 0.0 <= value <= 1.0
            return is_percentage
        return False

    @property
    def X0(self) -> float:
        return self._coords[0]

    @property
    def Y0(self) -> float:
        return self._coords[1]

    @property
    def X1(self) -> float:
        return self._coords[2]

    @property
    def Y1(self) -> float:
        return self._coords[3]

    @X0.setter
    def X0(self, value: float):
        self._coords[0] = value

    @Y0.setter
    def Y0(self, value: float):
        self._coords[1] = value

    @X1.setter
    def X1(self, value: float):
        self._coords[2] = value

    @Y1.setter
    def Y1(self, value: float):
        self._coords[3] = value

    @property
    def x0(self) -> int:
        if self._is_percentage(self.X0):
            scaled = self._scale(self.X0, self.parent.width)
            return scaled
        return int(self.X0)

    @property
    def y0(self) -> int:
        if self._is_percentage(self.Y0):
            scaled = self._scale(self.Y0, self.parent.height)
            return scaled
        return int(self.Y0)

    @property
    def x1(self) -> int:
        if self._is_percentage(self.X1):
            return self._scale(self.X1, self.parent.width)
        return int(self.X1)

    @property
    def y1(self) -> int:
        if self._is_percentage(self.Y1):
            return self._scale(self.Y1, self.parent.height)
        return int(self.Y1)

    @property
    def width(self) -> int:
        return self.x1 - self.x0 + 1

    @property
    def height(self) -> int:
        return self.y1 - self.y0 + 1
    
    @x0.setter
    def x0(self, value: int):
        self.X0 = value

    @y0.setter
    def y0(self, value: int):
        self.Y0 = value

    @x1.setter
    def x1(self, value: int):
        self.X1 = value

    @y1.setter
    def y1(self, value: int):
        self.Y1 = value

    @width.setter
    def width(self, value: int):
        if value < 1:
            raise ValueError(f"Width cannot be negative or zero {value}")
        self.X1 = self.X0 + value - 1

    @height.setter
    def height(self, value: int):
        if value < 1:
            raise ValueError(f"Height cannot be negative or zero {value}")
        self.Y1 = self.Y0 + value - 1

    def __add__(self, other: 'PMRect') -> 'PMRect':
        return PMRect(
            self.x0 + other.x0,
            self.y0 + other.y0,
            self.x1 + other.x1,
            self.y1 + other.y1
        )

    def move(self, x0: int, y0: int) -> 'PMRect':
        """Move the rectangle to (x0, y0)."""
        width = self.width
        height = self.height
        self[0] = x0
        self[1] = y0
        self[2] = x0 + width
        self[3] = y0 + height
        return self

    def rmove(self, dx: int, dy: int) -> 'PMRect':
        """Move the rectangle by dx and dy."""
        self[0] += dx
        self[1] += dy
        self[2] += dx
        self[3] += dy
        return self

    def __hash__(self):
        return hash((self.x0, self.y0, self.x1, self.y1))
    
    def __eq__(self, other: 'PMRect') -> bool:
        return (self.x0 == other.x0 and self.y0 == other.y0 and
                self.x1 == other.x1 and self.y1 == other.y1)

    def __str__(self):
        return f"PMRect({self.x0}, {self.y0}, {self.x1}, {self.y1})"
    
    def __repr__(self):
        return f"PMRect({self.x0}, {self.y0}, {self.x1}, {self.y1})"

    def contains(self, x: int, y: int) -> bool:
        return self.x0 <= x < self.x1 and self.y0 <= y < self.y1

    def intersects(self, other: 'PMRect') -> bool:
        return not (self.x1 <= other.x0 or self.x0 >= other.x1 or
                    self.y1 <= other.y0 or self.y0 >= other.y1)

    def to_tuple(self) -> tuple:
        return (self.x0, self.y0, self.x1, self.y1)

    @staticmethod
    def from_dims(dims: tuple) -> 'PMRect':
        """Create a PMRect from normalized dimensions."""
        if len(dims) != 4:
            raise ValueError("Dimensions must be a tuple of four elements (x0, y0, x1, y1).")
        rect = (
            int((dims[0] * 100) - 1),  # Assuming dims are normalized between 0 and 1
            int((dims[1] * 100) - 1),
            int((dims[2] * 100) - 1),
            int((dims[3] * 100) - 1)
        )
        return PMRect(*rect)

    @staticmethod
    def from_string(position: str) -> 'PMRect':
        """Create a PMRect from a position string."""
        x0, y0, x1, y1 = position.split(",")
        return PMRect(
            int(x0),
            int(y0),
            int(x1),
            int(y1)
        )