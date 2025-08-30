from dataclasses import dataclass
import requests
import copy

from pymirror.pmcard import PMCard
from pymirror.utils import SafeNamespace, expand_dict
from pymirror.pmtimer import PMTimer
from pymirror.pmwebapi import PMWebApi
from pymirror.pmlogger import _debug, _print, _error

class WebApiModule(PMCard):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._web_api = config.web_api
		self.api = PMWebApi(self._web_api.url, self._web_api.poll_secs, self._web_api.cache_file)
		self.display_timer = PMTimer(self._web_api.cycle_seconds * 1000)

		self.response = None
		self.items = []
		self.item_number = 0
		self.update(None, "(loading...)", None)  # Initialize with empty strings
		self.subscribe("KeyboardEvent")

	def _read_items(self, force: bool = False) -> int:
		context = {
			"_n_": 0,
			"payload": self.response,
		}
		self.items = []

		 # extract the maximum number of items to display
		display = copy.copy(self._web_api.display.__dict__)
		expand_dict(display, context)
		max_items = int(display.get("max", "1"))
		total_items = int(display.get("total", "1"))
		if total_items > max_items:
			total_items = max_items
		for n in range(total_items):
			context["_n_"] = n
			display = copy.copy(self._web_api.display.__dict__)
			expand_dict(display, context, "__error__") # extract the 'nth' item to display
			# if any of the display fields are "__error__", skip this item
			if "__error__" in display.values():
				continue
			self.items.append(display)
		return len(self.items)
	
	def _read_api(self):
		self.api.httpx.params = self._web_api.params.__dict__
		self.response = self.api.fetch_json(blocking=False)
		if not self.response:
			_error(f"Error fetching data")
			return False
		self._read_items()

	def _display_next_item(self):
		if not self.items:
			return
		if self.item_number >= len(self.items):
			self.item_number = 0
		self.header = self.items[self.item_number].get("header", "")
		self.body = self.items[self.item_number].get("body", "")
		self.footer = self.items[self.item_number].get("footer", "") 
		if self.api.is_from_cache():
			self.footer = f"(from cache: {self.api.last_date})\n{self.footer}"
		if self.body in [None, "", "None"]:
			self.body = self.header
			self.header = ""
		self.update(self.header, self.body, self.footer)
		self.item_number += 1
	
	def onKeyboardEvent(self, event):
		if event.
		pass

	def exec(self) -> bool:
		update = super().exec()

		if self.response == None or self.display_timer.is_timedout():
			self.result = self._read_api()
			self._display_next_item()
			self.display_timer.reset()
			update = True

		return update
