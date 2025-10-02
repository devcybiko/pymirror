from dataclasses import dataclass

@dataclass
class CliConfig:
    cycle_seconds: str
    command: str
    header: str
    body: str
    footer: str

