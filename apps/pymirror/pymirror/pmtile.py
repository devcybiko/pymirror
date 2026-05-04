from abc import ABC, abstractmethod
import ast

# from configs.config_config import ConfigConfig
from glslib.glsdb import GLSDb
from pmgfxlib.pmbitmap import PMBitmap
from pymirror.pmtimer import PMTimer
from pymirror.pymirror import PyMirror
from glslib.to_types import to_munch
from glslib.logger import _trace, _debug
from pymirror.pmrect import PMRect

from dataclasses import dataclass, field

from mixins.font_mixin import FontMixin
from mixins.gfx_mixin import GfxMixin
from mixins.text_mixin import TextMixin

@dataclass
class TileConfig(GfxMixin, FontMixin, TextMixin):
    ## tiledef
    clazz: str = field(default=None, metadata={"json_key": "class"})
    name: str = None
    position: str = "None"
    subscriptions: list[str] = None
    disabled: bool = False
    force_render: bool = False
    force_update: bool = False
    debug: bool = False
    force: bool = False
    clear: bool = False ## clear the framebuffer before writing
    refresh_time:str = "60s"

class PMTile(ABC):
    def __init__(self, pm: PyMirror, config):
        from glslib.gson import json_print
        self._config = config
        # GLS - need to remove this dependency on pm
        self.pm = pm
        self.pmdb: GLSDb = pm.pmdb
        json_print(config)
        self._tiledef: TileConfig = config.tile
        _tiledef: TileConfig = self._tiledef
        self.screen = pm.screen
        self.tile_n = 0 ## PyMirror sets this to the index in the pm.tiles list
        self.name = _tiledef.name or self.__class__.__name__
        self.position = _tiledef.position
        self.disabled = _tiledef.disabled
        self.force_render = _tiledef.force_render
        self.force_update = _tiledef.force_update
        self.timer = PMTimer(_tiledef.refresh_time, 1)
        self.subscriptions = []
        self.dirty = False
        self.focus = False

        self._time = 0.0  # time taken for tile execution
        self.bitmap = None
        rect = self._compute_rect(self.position)
        if rect:
            self.bitmap = PMBitmap(rect.width, rect.height, _tiledef)
            self.bitmap.rect = rect
            self.bitmap.gfx.set_font(_tiledef.font_name, _tiledef.font_size)
        self.subscribe(_tiledef.subscriptions or [])

    def _gfx_push(self):
        gfx = self.bitmap.gfx_push()
        return self.bitmap, gfx
    
    def _gfx_pop(self):
        return self.bitmap.gfx_pop()

    def _compute_rect(self, position: str = None) -> tuple:
        # compute rect based on "position"
        rect = PMRect(0,0,0,0)
        if not position or position == "None": return None
        if "," in position:
            # position is a string with comma-separated values
            # e.g. "0.25,0.15,0.75,0.85" - using percentages of the screen size
            # e.g. "100,100,300,300" - using absolute pixel values
            dims = [ast.literal_eval(x) for x in position.split(",")]
            if len(dims) != 4:
                raise ValueError(f"Invalid position format: {position}. Expected 4 comma-separated values.")
            rect = PMRect(dims[0], dims[1], dims[2], dims[3], self.pm.screen.rect)
            # rect = PMRect(
            #     int((self.pm.screen.bitmap.width - 1) * dims[0]),
            #     int((self.pm.screen.bitmap.height - 1) * dims[1]),
            #     int((self.pm.screen.bitmap.width - 1) * dims[2]),
            #     int((self.pm.screen.bitmap.height - 1) * dims[3])
            # )
            return rect
        dim_str = self.pm._config.positions[position]
        _trace(f"Tile {self._tiledef.name} position: {position}, dimensions: {dim_str}")
        if dim_str:
            _debug(f"Tile {self._tiledef.name} position: {position}, dimensions: {dim_str}")
            dims = [float(x) for x in dim_str.split(",")]
            ## this is the bounding box for the tile on-screen
            ## x0, y0 is the top-left corner, x1, y1 is the bottom-right corner
            ## these are in percentages of the screen size
            ## so we need to multiply to get the actual pixel values
            rect = PMRect(
                int((self.pm.screen.bitmap.width - 1) * dims[0]),
                int((self.pm.screen.bitmap.height - 1) * dims[1]),
                int((self.pm.screen.bitmap.width - 1) * dims[2]),
                int((self.pm.screen.bitmap.height - 1) * dims[3])
            )
        return rect
    
    def _allocate_bitmap(self):
        if not self.gfx.rect:
            _debug(f"Tile {self._tiledef.name} has no rect defined, cannot allocate bitmap.")
            return None
        width = self.gfx.x1 - self.gfx.x0 + 1
        height = self.gfx.y1 - self.gfx.y0 + 1
        _debug(f"Allocating bitmap for tile {self._tiledef.name} at {self.gfx.rect} with size {width}x{height}")
        return PMBitmap(width, height)

    @abstractmethod
    def render(self, force: bool = False) -> bool:
        """ Render the tile on its bitmap.
        returns True if the bitmap was updated, and needs a flush() call.
        If force is True, the tile should always render, even if nothing changed.
        """
        pass

    @abstractmethod
    def exec(self) -> bool:
        """ Execute the tile logic.
        returns True if the tile state changed, and needs a render() call.
        """
        pass

    def onEvent(self, event) -> None:
        """ Handle an event.
        This is called by the PM when an event is dispatched to the tile.
        Override this method to handle specific events.
        """
        self.dispatchEvent(event)

    def subscribe(self, event_names):
        if isinstance(event_names, str):
            event_names = [event_names]
        for event_name in event_names:
            self.subscriptions.append(event_name)

    def take_focus(self, state=True):
        self.focus = state
        self.dirty = True

    def has_focus(self):
        return self.focus

    def render_focus(self):
        _debug("render_focus:", self.name, self.focus)
        if not self.focus:
            return
        gfx = self.bitmap.gfx_push()
        gfx.color = "#ff0"
        gfx.line_width = 5
        rect = PMRect(0, 0, self.bitmap.rect.width - 1, self.bitmap.rect.height - 1)
        self.bitmap.rectangle(rect, fill=None)
        self.bitmap.gfx_pop()
        
    def is_subscribed(self, event_name):
        return event_name in self.subscriptions

    def dispatchEvent(self, event) -> None:
        method_name = f"on{event.event}"
        method = getattr(self, method_name, None)
        if method:
            method(event)
        else:
            _debug(f"No handler for event {event.event} in tile {self._tiledef.name}")

    def publish_event(self, event) -> None:
        """ Publish an event to the PM.
        This is used to notify the PM of an event that occurred in the tile.
        """
        self.pm.publish_event(to_munch(event))