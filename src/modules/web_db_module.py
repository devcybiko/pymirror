import time
import copy

from pymirror.pmcard import PMCard
from utils.utils import expand_dict, json_loads, to_dict
from pymirror.pmtimer import PMTimer
from pmlogger import _debug
from tables.web_api_table import WebApiTable

class WebDbModule(PMCard):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._web_db = config.web_db
		self.display_timer = PMTimer(self._web_db.cycle_time)
		self.dirty = False
		self.text = None
		self.last_text = None
		self.last_time = None
		self.response = None
		self.update(None, "(loading...)", None)  # Initialize with empty strings
		self.subscribe("KeyboardEvent")
		self.items = []

	def _parse_items(self, force: bool = False) -> int:
		_debug("_parse_items")
		context = {
			"_n_": 0,
			"payload": self.response,
		}
		self.items = []

		 # extract the maximum number of items to display
		template_dict = copy.copy(self._web_db.display)
		expand_dict(template_dict, context)
		max_items = int(template_dict.get("max", "1"))
		total_items = int(template_dict.get("total", "1"))
		if total_items > max_items:
			total_items = max_items
		for n in range(total_items):
			context["_n_"] = n
			template_dict = copy.copy(self._web_db.display)
			expand_dict(template_dict, context, "__error__") # extract the 'nth' item to display
			# if any of the display fields are "__error__", skip this item
			if "__error__" in template_dict.values():
				continue
			self.items.append(template_dict)
		self.item_number = 0
		return len(self.items)
	
	def _read_db(self):
		_debug("_read_db")
		record = self.pmdb.get_where(WebApiTable, WebApiTable.name == self.name)
		if record == None:
			_debug("... db.get_where() returns None")
			return
		_debug(to_dict(record))
		self.text = record.result_text
		if not self.text:
			_debug("... db.get_where() returns None")
			return
		if self.last_text == self.text:
			_debug("... db.get_where() returns same value")
			return
		self.last_text = self.text
		self.last_time = record.last_time
		self.response = json_loads(self.text)
		_debug("... new response... let's parse it")
		self._parse_items()

	def _display_next_item(self):
		_debug("_display_next_item")
		if not self.items:
			_debug("No items to display")
			return
		if self.item_number >= len(self.items):
			self.item_number = 0
		if self.item_number < 0:
			self.item_number = len(self.items)-1
		self.header = self.items[self.item_number].get("header", "")
		self.body = self.items[self.item_number].get("body", "")
		self.footer = self.items[self.item_number].get("footer", "") 
		if self.last_time:
			dt = self.last_time.strftime("%Y-%m-%d %H:%M:%S")
			self.footer = f"(from db: {dt})\n{self.footer}"
		if self.body in [None, "", "None"]:
			self.body = self.header
			self.header = ""
		self.update(self.header, self.body, self.footer)
		self.item_number += 1
	
	def onKeyboardEvent(self, event):
		if event.key_name == "KEY_LEFT":
			self.item_number -= 1
			self.dirty = True
			self.response = None ## HACK - this forces a redisplay... questionable
		if event.key_name == "KEY_RIGHT":
			self.item_number += 1
			self.dirty = True
			self.response = None ## HACK - this forces a redisplay... questionable

	def exec(self) -> bool:
		_debug("web_db_module dirty=", self.dirty)
		self.dirty = super().exec()
		_debug("...  dirty=", self.dirty)

		if self.display_timer.is_timedout():
			_debug("... timer: ", time.time(), self.display_timer.future_time)
			self._read_db()
			self._display_next_item()
			self.display_timer.reset()
			self.dirty = True

		return self.dirty
