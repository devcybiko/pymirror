from pymirror.pmmodule import PMModule
from pymirror.pmlogger import _debug

class WindowManagerModule(PMModule):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._window_manager = config.window_manager
        self.subscribe("RawKeyboardEvent")
        self.focus_module = None
        self.focus_module_n = 0

    def render(self, force: bool = False) -> bool:
        pass

    def exec(self):
        pass

    def find_focus_module(self):
        self.focus_module = None
        self.focus_module_n = 0
        for module in self.pm.modules:
            # find the module that has the focus
            if module.has_focus():
                self.focus_module = module
                break
            self.focus_module_n += 1
        return self.focus_module

    def _next_focus_module(self):
        focus_module = self.find_focus_module()
        if not focus_module:
            # either no current focus module
            # or no modules can take the focus
            # so start at the beginning and find the first one that can take the focus
            self.focus_module_n = 0
        next_focus_module = None
        next_focus_module_n = self.focus_module_n
        for _ in range(0, len(self.pm.modules)):
            next_focus_module_n = (next_focus_module_n + 1) % len(self.pm.modules)
            if hasattr(self.pm.modules[next_focus_module_n], "onKeyboardEvent"):
                next_focus_module = self.pm.modules[next_focus_module_n]
                break
        return next_focus_module

    def assign_focus(self, new_focus_module):
        if self.focus_module:
            self.focus_module.take_focus(False)
        self.focus_module = new_focus_module
        self.focus_module.take_focus(True)

    def onRawKeyboardEvent(self, event):
        _debug("window_manager", event)
        if event.key_name in ["KEY_TAB", "KEY_UP", "KEY_DOWN"]:
            # find the next focus module, or choose the first one if none are picked
            if event.pressed and not event.repeat:
                next_focus_module = self._next_focus_module()
                self.assign_focus(next_focus_module)
        else:
            if self.focus_module:
                # if we have a focus module selected... then send the keyboard event to it
                if event.pressed and not event.repeat:
                    event.event = "KeyboardEvent"
                    event.module = self.focus_module.name
                    _debug("... republishing event", event)
                    self.pm.publish_event(event)