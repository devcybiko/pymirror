from dataclasses import dataclass
from models.text_model import TextModel
from models.pmmodel import PMModel

@dataclass
class CardModel(PMModel):
    header: TextModel = None
    body: TextModel = None
    footer: TextModel = None
    timeout: int = 1
