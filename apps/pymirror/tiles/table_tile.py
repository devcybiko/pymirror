import copy

from munch import DefaultMunch
from pymirror.pmtile import PMTile
from components.pm_table_component import PMTableComponent

class TableTile(PMTile):
	def __init__(self, pm, config: DefaultMunch):
		super().__init__(pm, config)
		self._table_comp = PMTableComponent(self.bitmap.gfx, config.table, 0, 0, self.bitmap.width, self.bitmap.height)

	def render(self, force: bool = False) -> int:
		self._table_comp.render(self.bitmap)
		self._table_comp.clean()
		return True

	def exec(self):
		return self._table_comp.is_dirty()

