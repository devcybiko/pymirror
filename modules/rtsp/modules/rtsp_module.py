from dataclasses import dataclass
from datetime import datetime

from pyav_rtsp_grabber import PyAVRTSPGrabber
import pymirror.pmmodule

@dataclass
class RtspConfig:
    url: str
    refresh_time: str = "5s"

class RtspModule(pymirror.pmmodule.PMModule):
    url: str
    
    def __init__(self, pm, config: pymirror.pmmodule.ModuleConfig):
        super().__init__(pm, config)
        self._rtsp: RtspConfig = RtspConfig(**config.rtsp)
        self._rtsp
        
        self.url = self._rtsp.url
        self.grabber = PyAVRTSPGrabber(self.url, timeout=self._rtsp.refresh_time)
    
    def render(self, force=False):
       if self.frame is None:
           return False
       self.bitmap.clear()
       frame_bitmap = self.bitmap.from_image(self.frame)
       self.bitmap.paste(frame_bitmap)
       print(f"Rendered frame from {self.url} at {datetime.now()}")
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
        print(f"Captured frame from {self.url}", datetime.now())
        # Resize if needed (PIL Image.size is (width, height))
        if self.frame.size[0] != self.bitmap.width or self.frame.size[1] != self.bitmap.height:
            self.frame = self.frame.resize((self.bitmap.width, self.bitmap.height))

        return True
    
    def cleanup(self):
        """Cleanup on module shutdown"""
        self.grabber.disconnect()
