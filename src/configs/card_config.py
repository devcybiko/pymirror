from dataclasses import dataclass
from configs.text_config import TextConfig

@dataclass
class CardConfig:
    header: TextConfig = None
    body: TextConfig = None
    footer: TextConfig = None
    timeout: int = 1
