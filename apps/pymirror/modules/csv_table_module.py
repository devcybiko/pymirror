import copy

from munch import DefaultMunch
from configs.table_config import TableConfig
from pymirror.pmmodule import PMModule
from components.pm_table_component import PMCell, PMTableComponent

class CsvTableModule(PMModule):
	def __init__(self, pm, config: DefaultMunch):
		super().__init__(pm, config)
		self._csv_table = config.csv_table
		self.header, self.rows = self._read_csv(self._csv_table.fname)
		config_table = TableConfig(rows=len(self.rows), cols=len(self.header), height=self.bitmap.height, width=self.bitmap.width)
		self._table_comp = PMTableComponent(self.bitmap.gfx, config_table, 0, 0, self.bitmap.width, self.bitmap.height)
		self._table_comp.set_rows(self.rows)

	def _read_csv(self, fname: str) -> list:
		import csv
		rows = []
		header = None
		with open(fname, newline='') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				if header is None:
					header = row.keys()
				_row = []
				for k, v in row.items():
					cell = PMCell(value=v, format=None, halign="center", valign="center")
					_row.append(cell)
				rows.append(_row)
		return header, rows

	def render(self, force: bool = False) -> int:
		self._table_comp.render(self.bitmap)
		self._table_comp.clean()
		return True

	def exec(self):
		return self._table_comp.is_dirty()

