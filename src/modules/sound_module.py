from dataclasses import fields, is_dataclass
import pygame
from configs.module_config import ModuleConfig
from pymirror.pmmodule import PMModule
from pymirror.pmlogger import _error, _debug, _print

class SoundModule(PMModule):
    def __init__(self, pm, config: ModuleConfig):
        super().__init__(pm, config)
        self._sound = config
        self.subscribe(["SoundEvent"])
        # Initialize the mixer
        pygame.mixer.init()

    def render(self, force: bool = False) -> bool:
        pass

    def onSoundEvent(self, event):
        _debug(f"SoundModule: Playing sound {event.filename}")
        try:
            pygame.mixer.music.load(event.filename)
            pygame.mixer.music.play()
        except Exception as e:
            _error(f"Error playing sound {event.filename}: {e}")

    def exec(self) -> bool:
        # This module does not need to execute anything periodically
        return False

if __name__ == "__main__":
    pygame.mixer.init()
    sound = pygame.mixer.Sound("./sounds/signal.wav") # Replace with your sound file
    channel = sound.play() # Play the sound and get the Channel object
    while channel.get_busy():
        pygame.time.delay(100) # Add a small delay to prevent high CPU usage
    _print("Sound finished playing.")
