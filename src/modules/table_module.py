import copy
from pymirror.pmmodule import PMModule
from utils.utils import SafeNamespace
from pymirror.comps.pmtablecomp import PMTableComp

class TableModule(PMModule):
	def __init__(self, pm, config: SafeNamespace):
		super().__init__(pm, config)
		self._table_comp = PMTableComp(self.bitmap.gfx, config.table, 0, 0, self.bitmap.width, self.bitmap.height)

	def render(self, force: bool = False) -> int:
		self._table_comp.render(self.bitmap)
		self._table_comp.clean()
		return True

	def exec(self):
		return self._table_comp.is_dirty()

