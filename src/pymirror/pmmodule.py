from abc import ABC, abstractmethod
import copy
from dataclasses import dataclass

from pmgfxlib.pmbitmap import PMBitmap, PMGfx
from pymirror.pmtimer import PMTimer
from pymirror.utils import SafeNamespace, _height, _width, from_dict, non_null
from pymirror.pmlogger import _trace, _debug
from pymirror.pmrect import PMRect

@from_dict
@dataclass
class PMModuleDef(ABC):
	name: str = None
	position: str = "None"
	color: str = "#fff"
	bg_color: str = None
	text_color: str = "#fff"
	text_bg_color: str = None
	font_name: str = "DejaVuSans"
	font_size: int = 64
	subscriptions: list[str] = None
	disabled: bool = False
	force_render: bool = False
	force_update: bool = False

class PMModule(ABC):
	def __init__(self, pm, config: SafeNamespace):
		self._config = config
		# GLS - need to remove this dependency on pm
		self.pm = pm
		self._moddef = _moddef = PMModuleDef.from_dict(config.moddef.__dict__)
		self.screen = pm.screen
		self.
		self.name = _moddef.name or self.__class__.__name__
		self.position = _moddef.position
		self.disabled = _moddef.disabled
		self.force_render = _moddef.force_render
		self.force_update = _moddef.force_update
		self.timer = PMTimer(0, 0)
		self.subscriptions = []
		self._time = 0.0  # time taken for module execution
		self.bitmap = None
		rect = self._compute_rect(self.position)
		if rect:
			self.bitmap = PMBitmap(rect.width, rect.height, _moddef.__dict__)
			self.bitmap.rect = rect
			# gfx.color = non_null(_moddef.color, self.screen.bitmap.gfx.color, gfx.color)
			# gfx.bg_color = non_null(_moddef.bg_color, self.screen.bitmap.gfx.bg_color, gfx.bg_color)
			# gfx.text_color = non_null(_moddef.text_color, self.screen.bitmap.gfx.text_color, gfx.text_color)
			# gfx.text_bg_color = non_null(_moddef.text_bg_color, self.screen.bitmap.gfx.text_bg_color, gfx.text_bg_color)
			# font_name = non_null(_moddef.font_name, self.screen.bitmap.gfx.font_name, gfx.font_name)
			# font_size = non_null(_moddef.font_size, self.screen.bitmap.gfx.font_size, gfx.font_size)
			# gfx.set_font(font_name, font_size)
		self.subscribe(_moddef.subscriptions or [])

	def _compute_rect(self, position: str = None) -> tuple:
		# compute rect based on "position"
		rect = PMRect(0,0,0,0)
		if not position or position == "None": return None
		if "," in position:
			# position is a string with comma-separated values
			# e.g. "0.25,0.15,0.75,0.85"
			dims = [float(x) for x in position.split(",")]
			if len(dims) != 4:
				raise ValueError(f"Invalid position format: {position}. Expected 4 comma-separated values.")
			rect = PMRect(
				int((self.pm.screen.bitmap.width - 1) * dims[0]),
				int((self.pm.screen.bitmap.height - 1) * dims[1]),
				int((self.pm.screen.bitmap.width - 1) * dims[2]),
				int((self.pm.screen.bitmap.height - 1) * dims[3])
			)
			return rect
		dim_str = self.pm._config.positions[position]
		_trace(f"Module {self._moddef.name} position: {position}, dimensions: {dim_str}")
		if dim_str:
			_debug(f"Module {self._moddef.name} position: {position}, dimensions: {dim_str}")
			dims = [float(x) for x in dim_str.split(",")]
			## this is the bounding box for the module on-screen
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
			_debug(f"Module {self._moddef.name} has no rect defined, cannot allocate bitmap.")
			return None
		width = self.gfx.x1 - self.gfx.x0 + 1
		height = self.gfx.y1 - self.gfx.y0 + 1
		_debug(f"Allocating bitmap for module {self._moddef.name} at {self.gfx.rect} with size {width}x{height}")
		return PMBitmap(width, height)

	@abstractmethod
	def render(self, force: bool = False) -> bool:
		""" Render the module on its bitmap.
		returns True if the bitmap was updated, and needs a flush() call.
		If force is True, the module should always render, even if nothing changed.
		"""
		pass

	@abstractmethod
	def exec(self) -> bool:
		""" Execute the module logic.
		returns True if the module state changed, and needs a render() call.
		"""
		pass

	def onEvent(self, event) -> None:
		""" Handle an event.
		This is called by the PM when an event is dispatched to the module.
		Override this method to handle specific events.
		"""
		self.dispatchEvent(event)

	def subscribe(self, event_names):
		if isinstance(event_names, str):
			event_names = [event_names]
		for event_name in event_names:
			self.subscriptions.append(event_name)

	def is_subscribed(self, event_name):
		return event_name in self.subscriptions

	def dispatchEvent(self, event) -> None:
		method_name = f"on{event.event}"
		method = getattr(self, method_name, None)
		if method:
			method(event)
		else:
			_debug(f"No handler for event {event.event} in module {self._moddef.name}")

	def publish_event(self, event) -> None:
		""" Publish an event to the PM.
		This is used to notify the PM of an event that occurred in the module.
		"""
		self.pm.publish_event(event)