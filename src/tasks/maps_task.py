from os import path
from pmtaskmgr.pmtask import PMTask
from pmlogger import _debug, _error, _print

from staticmap import StaticMap, CircleMarker

class MapsTask(PMTask):
    def __init__(self, pmtm, config):
        super().__init__(pmtm, config)
        self.maps = self._task.maps
        self.url = self._task.url
        self.output_dir =self._task.output_dir

    def exec(self):
        for map_config in self.maps:
            fname = path.join(self.output_dir, map_config.fname)
            ## if fname exists
            if path.exists(fname):
                _debug(f"Map {fname} already exists, skipping")
                continue
            width = map_config.width
            height = map_config.height
            url = self.url
            longitude = float(map_config.lon)
            latitude = float(map_config.lat)
            zoom = int(map_config.zoom)
            m = StaticMap(width, height, url_template=url)
            m.add_marker(CircleMarker((longitude, latitude), 'red', 12))
            map_image = m.render(zoom=zoom).convert("RGBA")
            map_image.save(fname)
            print("Saved", fname)
