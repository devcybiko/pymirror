import copy

from munch import DefaultMunch
from glslib.glsdb import GLSDb
from pymirror.pmtile import PMTile
from components.pm_table_component import PMCell, PMTableComponent, TableConfig
from dataclasses import dataclass
from mixins.font_mixin import FontMixin
from mixins.text_mixin import TextMixin

@dataclass
class SqlTableConfig(TextMixin, FontMixin):
    sql: str = None
    sql_file: str = None
    sql_params: dict = None
    database_url: str = None

class SqlTableTile(PMTile):
	def __init__(self, pm, config: DefaultMunch):
		super().__init__(pm, config)
		self._sql_table: SqlTableConfig = pm.configurator.from_dict(config.sql_table, SqlTableConfig)
		self.db = GLSDb(self._sql_table.database_url)
		if self._sql_table.sql_file:
			with open(self._sql_table.sql_file, "r") as f:
				self._sql_table.sql = f.read()
			if self._sql_table.sql_params:
				self._sql_table.sql = self._sql_table.sql.format(**self._sql_table.sql_params)

	def _create_table(self, config) -> TableConfig:
		if hasattr(config, "table"):
			_config = self.pm.configurator.from_dict(config.table, TableConfig)
		else:
			_config = TableConfig()
		_config.header = self.header
		_config.rows = _config.rows or len(self.rows)
		_config.cols = _config.cols or (len(self.header) if self.header else 3)
		_config.height = _config.height or self.bitmap.height
		_config.width = _config.width or self.bitmap.width
		_config.row_height = _config.row_height or (self.bitmap.height // _config.rows)
		_config.col_width = _config.col_width or (self.bitmap.width // _config.cols)
		table = PMTableComponent(self.bitmap.gfx, _config, 0, 0, self.bitmap.width, self.bitmap.height)
		return table
	
	def _read_sql(self, query) -> list:
		rows = []
		data = self.db.query(query)
		i = 0
		row_colors = ["#010", "#030"]
		header = None
		for row in data:
			if header is None:
				header = list(row.keys())
			_row = []
			for k, v in row.items():
				cell = PMCell(value=v, format=None, halign="center", valign="center", bg_color=row_colors[i//2% len(row_colors)], text_color="#fff")
				_row.append(cell)
			rows.append(_row)
			i = i + 1
		return header, rows

	def render(self, force: bool = False) -> int:
		self.pmtable.render(self.bitmap)
		self.pmtable.clean()
		return True

	def exec(self):
		if not self.timer.is_timedout():
			return False
		self.timer.reset()
		self.header, self.rows = self._read_sql(self._sql_table.sql)
		self.pmtable: PMTableComponent = self._create_table(self._config)
		self.pmtable.set_rows(self.rows)
		return True

