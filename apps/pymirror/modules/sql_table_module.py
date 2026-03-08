import copy

from munch import DefaultMunch
from configs.sql_table_config import SqlTableConfig
from configs.table_config import TableConfig
from glslib.glsdb import GLSDb
from pymirror.pmmodule import PMModule
from pymirror.comps.pmtablecomp import PMCell, PMTableComp

class SqlTableModule(PMModule):
	def __init__(self, pm, config: DefaultMunch):
		super().__init__(pm, config)
		self._sql_table: SqlTableConfig = pm.configurator.from_dict(config.sql_table, TableConfig)
		db_config = DefaultMunch(url=self._sql_table.database_url)
		self.db = GLSDb(db_config)
		self.header, self.rows = self._read_sql(self._sql_table.sql)
		self._table_comp: PMTableComp = self._create_table(config)
		self._table_comp.set_rows(self.rows)

	def _create_table(self, config) -> TableConfig:
		if hasattr(config, "table"):
			_config = self.pm.configurator.from_dict(config.table, TableConfig)
		else:
			_config = TableConfig()
		print(22, "Creating table with config:", vars(config))
		_config.rows = _config.rows or len(self.rows)
		_config.cols = _config.cols or (len(self.header) if self.header else 3)
		_config.height = _config.height or self.bitmap.height
		_config.width = _config.width or self.bitmap.width
		_config.row_height = _config.row_height or (self.bitmap.height // _config.rows)
		_config.col_width = _config.col_width or (self.bitmap.width // _config.cols)
		table = PMTableComp(self.bitmap.gfx, _config, 0, 0, self.bitmap.width, self.bitmap.height)
		return table
	
	def _read_sql(self, query) -> list:
		rows = []
		header = None
		data = self.db.query(query)
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

