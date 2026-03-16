from glslib.crontab import Crontab
from pymirror.pmmodule import PMModule
from glslib.logger import _debug

from dataclasses import dataclass, field
from typing import List

@dataclass
class AlertConfig:
    cron: str
    description: str = None
    event: dict = field(default_factory=dict)

@dataclass
class CronConfig:
    alerts: List[AlertConfig] = field(default_factory=lambda: [AlertConfig(cron="*:00")])

class CronModule(PMModule):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._cron: CronConfig = pm.configurator.from_dict(config.cron, CronConfig)
		self.alerts = self._cron.alerts or []
		if type(self.alerts) is not list:
			self.alerts = [self.alerts]
		for alert in self.alerts:
			print(alert)
		self.crontab = Crontab([alert.cron for alert in self.alerts])

	def render(self, force: bool = False) -> bool:
		pass

	def exec(self):
		alert_indexes = self.crontab.check()
		if not alert_indexes:
			return
		for i in alert_indexes:
			alert = self.alerts[i]
			_debug(f"Alert triggered: {alert.event}")
			self.publish_event(alert.event)
		return False