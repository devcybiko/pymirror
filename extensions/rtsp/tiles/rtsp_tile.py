from dataclasses import dataclass
from datetime import datetime

from pmgfxlib.pmbitmap import PMBitmap
from pyav_rtsp_grabber import PyAVRTSPGrabber
import pymirror.pmtile

@dataclass
class RtspConfig:
    url: str
    refresh_time: str = "5s"
    scale: str = "fit"

class RtspTile(pymirror.pmtile.PMTile):
    url: str
    
    def __init__(self, pm, config: pymirror.pmtile.TileConfig):
        super().__init__(pm, config)
        self._rtsp: RtspConfig = RtspConfig(**config.rtsp)
        self._rtsp
        
        self.url = self._rtsp.url
        self.grabber = PyAVRTSPGrabber(self.url, timeout=self._rtsp.refresh_time)
    
    def render(self, force=False):
       if self.frame is None:
           return False
       self.bitmap.clear()
       frame_bitmap = PMBitmap().from_image(self.frame)
       frame_bitmap.scale(self.bitmap.width, self.bitmap.height, scale=self._rtsp.scale)
       self.bitmap.paste(frame_bitmap, halign="center", valign="center")
       return True

    def exec(self) -> bool:
        """Capture frame and update display"""
        if not self.timer.is_timedout():
            return False
        
        self.timer.reset(self._rtsp.refresh_time)
        
        # Get frame from RTSP stream
        self.frame = self.grabber.get_frame_pil()
        if self.frame is None:
            return False
        return True
    
    def cleanup(self):
        """Cleanup on module shutdown"""
        self.grabber.disconnect()
