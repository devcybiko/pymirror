from dataclasses import dataclass, field
from datetime import datetime
import importlib
import json
import os
import sys
import time
from dotenv import load_dotenv
import queue
import argparse
import traceback

from munch import DefaultMunch, Munch

from pymirror.pmlogger import trace, _debug, _debug, _info, _warning, _error, _critical, _trace
from pymirror.pmscreen import PMScreen
from pymirror.utils.utils import json_read, snake_to_pascal, expand_dict, SafeNamespace, to_munch
from pmserver.pmserver import PMServer
from pmdb.pmdb import PMDb
from pymirror.utils.pstat import get_pstat_delta, get_pids_by_cli

from events import * # get all events 

@dataclass
class PMStatus:
    debug: bool = False
    remote_display: str = None
    start_time: datetime = None
    taskmgr: DefaultMunch = field(default_factory=DefaultMunch)
    
def _to_null(s):
    """ Convert a string to None if it is 'null' or 'None' """
    if s in ["null", "None"]:
        return None
    return s

class PyMirror:
    def __init__(self, config_fname, args):
        ## by convention, all objects get a copy of the config
        ## so that they can access it without having to pass it around
        ## and they "pluck out" the values they need
        _debug(f"args: {args}")
        self._config = self._load_config(config_fname)
        if args.output_file:
            self._config.screen.output_file = _to_null(args.output_file)
        if args.frame_buffer:
            self._config.screen.frame_buffer = _to_null(args.frame_buffer)
        _debug(f"Using config: {self._config}")
        self.pmdb = PMDb(self._config.pmdb.__dict__) if self._config.pmdb else None
        self.screen = PMScreen(self._config.screen)
        self.force_render = False
        self.debug = self._config.debug
        self.modules = []
        self.events = []
        self.start_time = datetime.now()
        self.status = None
        self.get_status()
        self._clear_screen = True  # Flag to clear the screen on each loop
        self.server_queue = queue.Queue()  # Use a queue to manage events
        self._load_modules()
        self.server = PMServer(self._config.server, self.server_queue)
        self.server.start()  # Start the server to handle incoming events

    def get_status(self) -> PMStatus:
        if not self.status:
            self.status = PMStatus()
        self.status.debug = self.debug
        self.status.remote_display = self.screen._screen.output_file
        self.status.start_time = self.start_time
        pids = get_pids_by_cli("pmtaskmgr")
        if pids:
            self.status.taskmgr.pids = pids
            old_pstat = self.status.taskmgr.pstat
            self.status.taskmgr.pstat = get_pstat_delta(pids[0], old_pstat)
        else:
            self.status.taskmgr = DefaultMunch()
        return self.status

    def _load_config(self, config_fname) -> SafeNamespace:
        # read .env file if it exists
        load_dotenv()
        # Load the main configuration file
        config = json_read(config_fname)
        # Load secrets from .secrets file if specified
        secrets_path = config.get("secrets")
        if secrets_path:
            secrets_path = os.path.expandvars(secrets_path)
        else:
            secrets_path = ".secrets"
        load_dotenv(dotenv_path=secrets_path)
        # Expand environment variables in the config
        expand_dict(config, os.environ)
        return SafeNamespace(**config)

    def _load_modules(self):
        for module_config in self._config.modules:
            ## load the module dynamically
            if type(module_config) is str:
                ## if moddef is a string, it is the name of a module config file
                ## load the module definition from the file
                ## the file should be in JSON format
                try:
                    config = json_read(module_config)
                    expand_dict(config, {})  # Expand environment variables in the config
                    module_config = SafeNamespace(**config)
                except Exception as e:
                    _debug(f"Error loading module config from {module_config}: {e}")
                    sys.exit(1)
            ## import the module using its name
            ## all modules should be in the "modules" directory
            mod = importlib.import_module("modules."+module_config.module+"_module")
        
            ## get the class from inside the module
            ## convert the file name to class name inside the module
            ## by convention the filename is snake_case and the class name is PascalCase
            clazz_name = snake_to_pascal(module_config.module)
            print(f"Loading '{module_config.moddef.name}' module, class {clazz_name} from {mod.__name__}")
            clazz = getattr(mod, clazz_name + "Module", None)

            ## create an instance of the class (module)
            ## and pass the PyMirror instance and the module config to it
            ## See pymirror.PMModule for the expected constructor
            obj = clazz(self, module_config)

            ## update the module with its position in the pm.modules list
            obj.module_n = len(self.modules)

            ## add the module to the list of modules
            self.modules.append(obj)

    def _read_server_queue(self):
        ## add any messages that have come from the web server
        try:
            while event := self.server_queue.get(0):
                ## GLS - temporarily do an append
                self.events.append(event)
                _debug("queue: reading event:", event)
                # self.publish_event(event)
        except queue.Empty:
            # No new events in the queue
            pass

    def _send_events_to_module(self, module, events):
        if not module.subscriptions: 
            return
        for event in events:
            if event.event in module.subscriptions:
                if not event.module or event.module == module.name:
                    _debug(f"_send_events_to_module: _send_events_to_module to {module.name} event:", event)
                    module.onEvent(event)

    def _convert_events_to_namespace(self):
        """ Convert a list of events to SafeNamespace objects """
        return [SafeNamespace(**event) if isinstance(event, dict) else event for event in self.events]

    def _send_events_to_modules(self):
        if not self.events: return
        self.events = self._convert_events_to_namespace()  # Convert events to SafeNamespace if needed
        for module in self.modules:
            self._send_events_to_module(module, self.events)  # Send all events to the module
        self.events.clear()  # Clear the events after sending them

    def publish_event(self, event: dict):
        _debug("publish_event", event)
        ## should this go on a seperate event list?
        ## if a module sends an event from inside an event dispatcher
        ## then it may not get processed
        ## GLS - so for now we put it on the "server_queue"
        self.server_queue.put(to_munch(event))

        # if type(event) is dict:
        #     self.events.append(SafeNamespace(**event))
        # elif isinstance(event, SafeNamespace):
        #     self.events.append(event)
        # else:
        #     raise TypeError(f"Event must be a dict or SafeNamespace, got {type(event)}")

    def _stats_for_nerds(self, module):
        if not module.bitmap: 
            ## non-rendering modules will not have a bitmap (eg: cron)
            return
        sbm = self.screen.bitmap
        mbm = module.bitmap
        sgfx = sbm.gfx_push()
        sgfx.font.set_font("DejaVuSans", 24)
        sbm.rectangle(mbm.rect, fill=None)
        _time = module._time or 0.0
        sbm.text(f"{module._moddef.name} ({_time:.2f}s)", mbm.x0 + sgfx.line_width, mbm.y0 + sgfx.line_width)
        sbm.text_box(mbm.rect, f"{module._moddef.position}", halign="right", valign="top")
        self.screen.bitmap.gfx_pop()

    def full_render(self):
        self.screen.bitmap.clear()
        for module in reversed(self.modules):
            if module.disabled or not module.bitmap: continue
            module.render(force=True)
            self.screen.bitmap.paste(module.bitmap, module.bitmap.x0, module.bitmap.y0, mask=module.bitmap)
        if self.debug: self._stats_for_nerds(module)
        self.screen.flush()  # Flush the screen to show all modules at once

    def _exec_modules(self):
        modules_changed = []
        
        for module in self.modules:
            if not module.disabled:
                module._time = 0.0  # Reset the time for each module
                start_time = time.time()  # Start timing the module execution
                state_changed = module.exec() # update module state (returns True if the state has changed)
                end_time = time.time()  # End timing the module execution
                if state_changed or module.force_render: 
                    modules_changed.append(module)
                    module._time += end_time - start_time  # Calculate the time taken for module execution
        return modules_changed

    def _render_modules(self, modules_changed):
        """ Render all modules that have changed state """
        if self._clear_screen:
            _debug("self._clear_screen", self._clear_screen)
            self.full_render()
            self._clear_screen = False
            return

        for module in modules_changed:
            if (not module.disabled) and module.bitmap:
                start_time = time.time()  # Start timing the module rendering
                module.render(force=self.force_render)
                end_time = time.time()  # End timing the module rendering
                if module._time:
                    module._time += end_time - start_time  # add on the time taken for module rendering

    def _update_screen(self, modules_changed):
        updated = False
        for module in reversed(self.modules):
            if (not module.disabled) and module.bitmap and module in modules_changed:
                # print("... painting", module.name)
                start_time = time.time()  # Start timing the module rendering
                self.screen.bitmap.paste(module.bitmap, module.bitmap.x0, module.bitmap.y0, mask=module.bitmap)
                end_time = time.time()  # End timing the module rendering
                module._time += end_time - start_time  # add on the time taken for module rendering
                if self.debug: self._stats_for_nerds(module) # draw boxes around each module if debug is enabled
                updated = True
        if updated:
            self.screen.flush()

    def _time(self, fn, *args):
        t0 = time.time()
        result = fn(*args)
        t1 = time.time()
        _debug(getattr(fn, "__name__", repr(fn)), ":", f"{(t1-t0)*1000} ms")
        return result

    def run(self):
        try:
            while True:
                self._time(self._read_server_queue)
                self._time(self._send_events_to_modules)
                modules_changed = self._time(self._exec_modules)
                self._time(self._render_modules, modules_changed)
                self._time(self._update_screen, modules_changed)
                # _debug("---")
                time.sleep(0.001) # Sleep for a short time to give pmserver a chance to process web requests
                _debug("...")
        except Exception as e:
            traceback.print_exc()  # <-- This _debugs the full stack trace to stdout
            self._error_screen(e)  # Display the error on the screen

    def _error_screen(self, e):
        """ Display an error screen with the exception details """
        self.screen.bitmap.clear()
        gfx = self.screen.bitmap.gfx
        gfx.text_color = "#f00"
        gfx.text_bg_color = "#ff0"
        self.screen.bitmap.text_box(gfx.rect, f"Exception:\n\n{str(e)}")
        self.screen.flush()

    def _bsod(self, e):
        """ Blue Screen of Death """
        tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
        error_lines = [line.split("\n")[0] for line in tb_lines if line.lstrip().startswith("File ")]
        error_lines = "\n".join(error_lines)
        error_lines = str(e) + "\n\n" + error_lines
        self.screen.bitmap.clear()
        self.screen.gfx.text_color = "#ccc"
        self.screen.gfx.text_bg_color = "#00f"
        self.screen.gfx.font_name = "DejaVuSerif"
        self.screen.gfx.set_font(self.screen.gfx.font_name, 32)
        self.screen.bitmap.text_box(self.screen.gfx, f"Exception: {error_lines}", (0, 0, self.screen.gfx.width, self.screen.gfx.height), valign="center", halign="left")
        self.screen.flush()



def main():
    parser = argparse.ArgumentParser(description="PyMirror Smart Mirror Application")
    parser.add_argument(
        "-c", "--config",
        default="config.json",
        help="Path to config JSON file (default: config.json)"
    )
    parser.add_argument(
        "--frame_buffer",
        metavar="DEVICE",
        help="Frame buffer device path (e.g., /dev/fb0, /dev/fb1)"
    )
    parser.add_argument(
        "--output_file",
        metavar="PATH",
        help="Output file path for screen capture (supports .jpg, .png formats). "
            "Overrides the output_file setting in config."
    )
    args = parser.parse_args()

    pm = PyMirror(args.config, SafeNamespace(**vars(args)))
    pm.run()

if __name__ == "__main__":
    main()
