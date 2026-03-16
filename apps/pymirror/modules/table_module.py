import copy

from munch import DefaultMunch
from pymirror.pmmodule import PMModule
from components.pmtablecomp import PMTableComp

class TableModule(PMModule):
	def __init__(self, pm, config: DefaultMunch):
		super().__init__(pm, config)
		self._table_comp = PMTableComp(self.bitmap.gfx, config.table, 0, 0, self.bitmap.width, self.bitmap.height)

	def render(self, force: bool = False) -> int:
		self._table_comp.render(self.bitmap)
		self._table_comp.clean()
		return True

	def exec(self):
		return self._table_comp.is_dirty()

