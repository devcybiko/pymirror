from dataclasses import dataclass
from configs.alert_config import AlertConfig
from configs.analog_clock_config import AnalogClockConfig
from configs.card_config import CardConfig
from configs.cli_config import CliConfig
from configs.clock_config import ClockConfig
from configs.cron_config import CronConfig
from configs.csv_table_config import CsvTableConfig
from configs.fonts_config import FontsConfig
from configs.forecast_config import ForecastConfig
from configs.ical_config import IcalConfig
from configs.image_config import ImageConfig
from configs.module_config import ModuleConfig
from configs.openweathermap_config import OpenweathermapConfig
from configs.plot_config import PlotConfig
from configs.pmdb_config import PmdbConfig
from configs.slideshow_config import SlideshowConfig  # Missing import
from configs.sql_table_config import SqlTableConfig
from configs.status_config import StatusConfig        # Missing import
from configs.table_config import TableConfig            # Missing import
from configs.text_config import TextConfig            # Missing import
from configs.weather_config import WeatherConfig      # Missing import
from configs.web_db_config import WebDbConfig         # Missing import

@dataclass
class ConfigConfig:
    module: ModuleConfig
    alert: AlertConfig = None
    analog_clock: AnalogClockConfig = None
    card: CardConfig = None
    cli: CliConfig = None
    clock: ClockConfig = None
    cron: CronConfig = None
    csv_table: CsvTableConfig = None
    fonts: FontsConfig = None
    forecast: ForecastConfig = None
    ical: IcalConfig = None
    image: ImageConfig = None
    openweathermap: OpenweathermapConfig = None
    plot: PlotConfig = None
    pmdb: PmdbConfig = None
    slideshow: SlideshowConfig = None
    csv_table: CsvTableConfig = None
    sql_table: SqlTableConfig = None
    status: StatusConfig = None
    text: TextConfig = None
    table: TableConfig = None
    weather: WeatherConfig = None
    web_db: WebDbConfig = None

