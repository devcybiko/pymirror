from dataclasses import dataclass

@dataclass
class AlertConfig:
    header: str = None
    body: str = None
    footer: str = None
    timeout: int = 1
