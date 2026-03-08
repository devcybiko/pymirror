from dataclasses import dataclass

@dataclass
class AlertEvent:
	event: str = "AlertEvent"
	header: str = ""
	body: str = ""
	footer: str = ""
	timeout: int = 0
