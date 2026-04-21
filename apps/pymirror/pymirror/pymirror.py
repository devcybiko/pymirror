from dataclasses import dataclass, field
from datetime import datetime
import importlib
import os
import time
from dotenv import load_dotenv
import queue
import argparse
import traceback

from munch import DefaultMunch

from configs.pmconfig import PMConfig
from glslib.logger import _debug, _print, _die
from glslib.strftime import exemplar_date_time
from pymirror.pmscreen import PMScreen
from glslib.module_manager import TileManager
from glslib.strings import expand_dataclass, snake_to_pascal
from glslib.to_types import to_munch
from pmserver.pmserver import PMServer
from glslib.glsdb import GLSDb
from glslib.pstat import get_pstat_delta, get_pids_by_cli
import tiles ## import all tiles so that they get registered with the tileManager

from events import * # get all events 

# Now use merged_configs as your config namespace
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
        self.configurator = PMConfig()
        self._config = self._load_config(config_fname)
        if args.output_file:
            self._config.screen.output_file = _to_null(args.output_file)
        if args.frame_buffer:
            self._config.screen.frame_buffer = _to_null(args.frame_buffer)
        _debug(f"Using config: {self._config}")
        self._import_modules_from_config()
        self.pmdb = GLSDb(self._config.pmdb.url) if self._config.pmdb else None
        self.screen = PMScreen(self._config.screen)
        self.force_render = False
        self.debug = self._config.debug
        self.tiles = []
        self.events = []
        self.start_time = datetime.now()
        self.status = None
        self.get_status()
        self._clear_screen = True  # Flag to clear the screen on each loop
        self.server_queue = queue.Queue()  # Use a queue to manage events
        self._load_tiles()
        self.server = PMServer(self._config, self.server_queue)
        self.server.start()  # Start the server to handle incoming events

    def _import_modules_from_config(self):
        """ Import any tiles specified in the config file """
        for folder in self._config.imports:
            for package_name in ["configs", "tables", "tiles"]:
                TileManager.load_modules(folder, package_name)
    
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

    def _load_config(self, config_fname) -> dataclass:
        pmconfig = self.configurator
        # read .env file if it exists
        load_dotenv()
        # Load the main configuration file
        config = pmconfig.from_file(config_fname, with_config="pymirror")
        # Load secrets from .secrets file if specified
        secrets_path = config.secrets
        if secrets_path:
            secrets_path = os.path.expandvars(secrets_path)
        else:
            secrets_path = ".secrets"
        load_dotenv(dotenv_path=secrets_path)
        # Expand environment variables in the config
        expand_dataclass(config, os.environ)
        return config

    def _load_tiles(self):
        pmconfig = self.configurator
        for tile_config in self._config.tiles:
            ## load the tile dynamically
            print(110, f"Loading tile from config: {tile_config}")
            if type(tile_config) is str:
                ## if moddef is a string, it is the name of a tile config file
                ## load the tile definition from the file
                ## the file should be in JSON format
                tile_config = pmconfig.from_file(tile_config)
                expand_dataclass(tile_config, {})  # Expand environment variables in the config
            ## import the tile using its name
            ## all tiles should be in the "tiles" directory
            print(120, f"Loading tile from config: {tile_config}")
            clazz_name = tile_config.tile.clazz
            try:
                mod = importlib.import_module(f"tiles.{clazz_name}_tile")
            except ModuleNotFoundError as e:
                msg = f"Error importing tile 'tiles.{clazz_name}_tile': {e}"
                raise ImportError(f"{msg}\nBe sure to add the tile to your __init__.py file in the tiles directory.")
            ## get the class from inside the tile
            ## convert the file name to class name inside the tile
            ## by convention the filename is snake_case and the class name is PascalCase
            clazz_name = snake_to_pascal(clazz_name)
            _print(f"Loading '{tile_config.tile.name}' tile, class {clazz_name} from {mod.__name__}")
            clazz = getattr(mod, clazz_name + "Tile", None)
            if clazz is None:
                raise ImportError(f"Class '{clazz_name}tile' not found in tile '{mod.__name__}'")

            ## create an instance of the class (tile)
            ## and pass the PyMirror instance and the tile config to it
            ## See pymirror.PMtile for the expected constructor
            obj = clazz(self, tile_config)

            ## update the tile with its position in the pm.tiles list
            obj.tile_n = len(self.tiles)

            ## add the tile to the list of tiles
            self.tiles.append(obj)

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

    def _send_events_to_tile(self, tile, events):
        if not tile.subscriptions: 
            return
        for event in events:
            if event.event in tile.subscriptions:
                if not event.tile or event.tile == tile.name:
                    _debug(f"_send_events_to_tile: _send_events_to_tile to {tile.name} event:", event)
                    tile.onEvent(event)

    def _convert_events_to_namespace(self):
        """ Convert a list of events to DefaultMunch objects """
        return [DefaultMunch(**event) if isinstance(event, dict) else event for event in self.events]

    def _send_events_to_tiles(self):
        if not self.events: return
        self.events = self._convert_events_to_namespace()  # Convert events to DefaultMunch if needed
        for tile in self.tiles:
            self._send_events_to_tile(tile, self.events)  # Send all events to the tile
        self.events.clear()  # Clear the events after sending them

    def publish_event(self, event: dict):
        _debug("publish_event", event)
        ## should this go on a seperate event list?
        ## if a tile sends an event from inside an event dispatcher
        ## then it may not get processed
        ## GLS - so for now we put it on the "server_queue"
        self.server_queue.put(to_munch(event))

        # if type(event) is dict:
        #     self.events.append(DefaultMunch(**event))
        # elif isinstance(event, DefaultMunch):
        #     self.events.append(event)
        # else:
        #     raise TypeError(f"Event must be a dict or DefaultMunch, got {type(event)}")

    def _stats_for_nerds(self, tile):
        if not tile.bitmap: 
            ## non-rendering tiles will not have a bitmap (eg: cron)
            return
        sbm = self.screen.bitmap
        mbm = tile.bitmap
        sgfx = sbm.gfx_push()
        sgfx.font.set_font("DejaVuSans", 24)
        sbm.rectangle(mbm.rect, fill=None)
        _time = tile._time or 0.0
        sbm.text(f"{tile._moddef.name} ({_time:.2f}s)", mbm.x0 + sgfx.line_width, mbm.y0 + sgfx.line_width)
        sbm.text_box(mbm.rect, f"{tile._moddef.position}", halign="right", valign="top")
        self.screen.bitmap.gfx_pop()

    def full_render(self):
        self.screen.bitmap.clear()
        for tile in reversed(self.tiles):
            if tile.disabled or not tile.bitmap: continue
            tile.render(force=True)
            self.screen.bitmap.paste(tile.bitmap, tile.bitmap.x0, tile.bitmap.y0, mask=tile.bitmap)
        if self.debug: self._stats_for_nerds(tile)
        self.screen.flush()  # Flush the screen to show all tiles at once

    def _exec_tiles(self):
        tiles_changed = []
        
        for tile in self.tiles:
            if not tile.disabled:
                tile._time = 0.0  # Reset the time for each tile
                start_time = time.time()  # Start timing the tile execution
                state_changed = tile.exec() # update tile state (returns True if the state has changed)
                end_time = time.time()  # End timing the tile execution
                if state_changed or tile.force_render: 
                    tiles_changed.append(tile)
                    tile._time += end_time - start_time  # Calculate the time taken for tile execution
        return tiles_changed

    def _render_tiles(self, tiles_changed):
        """ Render all tiles that have changed state """
        if self._clear_screen:
            _debug("self._clear_screen", self._clear_screen)
            self.full_render()
            self._clear_screen = False
            return

        for tile in tiles_changed:
            if (not tile.disabled) and tile.bitmap:
                start_time = time.time()  # Start timing the tile rendering
                if tile._moddef.clear:
                    gfx = self.bitmap.gfx.push(tile.bitmap.gfx)
                    self.bitmap.rectangle(self.tile.bitmap.erect)
                tile.render(force=self.force_render)
                end_time = time.time()  # End timing the tile rendering
                if tile._time:
                    tile._time += end_time - start_time  # add on the time taken for tile rendering

    def _update_screen(self, tiles_changed):
        updated = False
        for tile in reversed(self.tiles):
            if (not tile.disabled) and tile.bitmap and tile in tiles_changed:
                start_time = time.time()  # Start timing the tile rendering
                self.screen.bitmap.paste(tile.bitmap, tile.bitmap.x0, tile.bitmap.y0, mask=tile.bitmap)
                end_time = time.time()  # End timing the tile rendering
                tile._time += end_time - start_time  # add on the time taken for tile rendering
                if self.debug: self._stats_for_nerds(tile) # draw boxes around each tile if debug is enabled
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
                self._time(self._send_events_to_tiles)
                tiles_changed = self._time(self._exec_tiles)
                self._time(self._render_tiles, tiles_changed)
                self._time(self._update_screen, tiles_changed)
                # _debug("---")
                time.sleep(0.01) # Sleep for a short time to give pmserver a chance to process web requests
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
        _die(f"Error displaying exception: {e}")  # Re-raise the exception after displaying it

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
    pm = PyMirror(args.config, DefaultMunch(**vars(args)))
    pm.run()

if __name__ == "__main__":
    main()
