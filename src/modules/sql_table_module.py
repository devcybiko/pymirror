import copy

from munch import DefaultMunch
from configs.table_config import TableConfig
from pmdb.pmdb import PMDb
from pymirror.pmmodule import PMModule
from utils.utils import SafeNamespace
from pymirror.comps.pmtablecomp import PMCell, PMTableComp

class SqlTableModule(PMModule):
	def __init__(self, pm, config: SafeNamespace):
		super().__init__(pm, config)
		self._sql_table = config.sql_table
		db_config = DefaultMunch(url=self._sql_table.database_url)
		self.turo_db = PMDb(db_config)
		self.header, self.rows = self._read_sql(self._sql_table.sql)
		config_table = TableConfig(rows=len(self.rows), cols=len(self.header), height=self.bitmap.height, width=self.bitmap.width, has_header=True)
		self._table_comp = PMTableComp(self.bitmap.gfx, config_table, 0, 0, self.bitmap.width, self.bitmap.height)
		self._table_comp.set_rows(self.rows)

	def _read_sql(self, query) -> list:
		rows = []
		header = None
		data = self.turo_db.raw_query(query)
		i = 0
		row_colors = ["#010", "#030"]
		for row in data:
			if header is None:
				header = list(row.keys())
				_row = [PMCell(value=h, format=None, halign="center", valign="center", bg_color="#050", text_color="#0f0") for h in header]
				rows.append(_row)
			_row = []
			for k, v in row.items():
				cell = PMCell(value=v, format=None, halign="center", valign="center", bg_color=row_colors[i//2% len(row_colors)], text_color="#fff")
				_row.append(cell)
			rows.append(_row)
			i = i + 1
		return header, rows

	def render(self, force: bool = False) -> int:
		self._table_comp.render(self.bitmap)
		self._table_comp.clean()
		return True

	def exec(self):
		return self._table_comp.is_dirty()

