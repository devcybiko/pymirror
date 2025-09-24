from datetime import datetime
from pymirror.pmmodule import PMModule
from pymirror.utils.utils import SafeNamespace, strftime_by_example

class ClockModule(PMModule):
	def __init__(self, pm, config: SafeNamespace):
		super().__init__(pm, config)
		self._clock = config.clock
		self.date_format = strftime_by_example(self._clock.date_format) or "%I:%M:%S %p"
		print("...", self.date_format)
		self.last_time = None
		self.curr_time = datetime.now().strftime(self.date_format)

	def render(self, force: bool = False) -> bool:
		self.bitmap.clear()
		self.bitmap.text_box((0, 0, self.bitmap.rect.width-1, self.bitmap.rect.height-1),
			self.curr_time,
			halign=self._clock.halign,
			valign=self._clock.valign)
		self.last_time = self.curr_time
		return True

	def exec(self) -> bool:
		# if date_format includes "%W" or "%U", update the week number
		# all this ceremony because %W and %U are zero-based and we must add 1 to them
		to_lower = False
		to_upper = False
		date_format = self.date_format
		if not date_format: return False
		if "%W" in date_format:
			date_format = date_format.replace("%W", "_W_")
		if "%U" in date_format:
			date_format = date_format.replace("%U", "_U_")

		# lower case the date format if it starts with "-"
		if date_format[0] == "-":
			date_format = date_format[1:]
			to_lower = True
		if date_format[0] == "+":
			date_format = date_format[1:]
			to_upper = True

		self.curr_time = datetime.now().strftime(date_format)

		if "_W_" in date_format:
			week_number = int(datetime.now().strftime("%W")) + 1
			self.curr_time = self.curr_time.replace("_W_", f"{week_number:02d}")
		if "_U_" in date_format:
			week_number = int(datetime.now().strftime("%U")) + 1
			self.curr_time = self.curr_time.replace("_U_", f"{week_number:02d}")
		if to_lower:
			self.curr_time = self.curr_time.lower()
		if to_upper:
			self.curr_time = self.curr_time.upper()

		return self.curr_time != self.last_time

