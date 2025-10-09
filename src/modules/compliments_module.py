from datetime import datetime
import random

from pymirror.pmmodule import PMModule
from utils.utils import expand_dict
from pymirror.pmcard import PMCard

class ComplimentsModule(PMModule):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._compliments = config.compliments
        self.timer.set_timeout(self._compliments.update_interval_secs * 1000)

    def _pick_complement(self):
        "Pick a random compliment based on the current time of day"
        # Get the current hour
        current_hour = datetime.now().hour
        if current_hour < self._compliments.afternoon_start_time:
            self.text = random.choice(self._compliments.morning)
        elif current_hour < self._compliments.evening_start_time:
            self.text = random.choice(self._compliments.afternoon)
        elif current_hour < self._compliments.night_start_time:
            self.text = random.choice(self._compliments.evening)
        else:
            self.text = random.choice(self._compliments.night)

    def render(self, force: bool = False) -> bool:
        self.bitmap.clear()
        self.bitmap.text_box( (0,0,self.bitmap.width,self.bitmap.height), self.text, valign="center", halign="center")
        self.last_text = self.text
        return True
    
    def exec(self) -> bool:
        if self.timer.is_timedout():
            self.timer.reset()
            self._pick_complement()
            return True
        return False
