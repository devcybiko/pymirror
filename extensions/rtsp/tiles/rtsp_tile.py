from dataclasses import dataclass
from datetime import datetime
import time

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
        self.url = self._rtsp.url
        self.frame = None
        self.last_frame = None
        self.retries = 0
        self.max_retries = 10
        self.grabber = PyAVRTSPGrabber(self.url, timeout=10)
    
    def _reconnect(self):
        self.retries += 1
        print(f"... lost connection to {self.url} (retry {self.retries}/{self.max_retries})")
        if self.retries >= self.max_retries:
            print(f"...reconnecting {self.url} after {self.max_retries} retries")
            timeout_seconds = 10
            deadline = time.monotonic() + max(2.0, timeout_seconds * 2)

            old_grabber = self.grabber
            self.grabber = PyAVRTSPGrabber(self.url, timeout=timeout_seconds)
            old_grabber = None
            self.frame = None

            # Block reconnect until we either get a frame or hit the timeout window.
            while time.monotonic() < deadline:
                frame = self.grabber._get_fresh_frame()
                if frame is not None:
                    self.frame = frame
                    print(f"Reconnect successful for {self.url}")
                    break
                time.sleep(0.2)

            if self.frame is None:
                print(f"Reconnect timed out for {self.url}")

            self.retries = 0
        return False

    def _parse_seconds(self, value: str | int | float) -> float:
        if isinstance(value, (int, float)):
            return max(1.0, float(value))

        value_str = str(value).strip().lower()
        if value_str.endswith("s"):
            value_str = value_str[:-1]

        try:
            return max(1.0, float(value_str))
        except (TypeError, ValueError):
            return 5.0

    def render(self, force=False):
        if self.frame is None:
            self.bitmap.clear()
            self.bitmap.text("No video feed", 0, 0)
            return False
        self.bitmap.clear()
        frame_bitmap = PMBitmap().from_image(self.frame)
        frame_bitmap.scale(self.bitmap.width, self.bitmap.height, scale=self._rtsp.scale)
        self.bitmap.paste(frame_bitmap, halign="center", valign="center")
        if self.last_frame:
            # compare self.fram and self.last_frame as PIL images, if they are the same return False
            if self.frame.tobytes() == self.last_frame.tobytes():
                print(f"Video feed frozen for {self.url}")
                self.bitmap.text("Video Frozen", 0, 0)
                self._reconnect()
                return False
        self.last_frame = self.frame
        self.retries = 0
        return True

    def exec(self) -> bool:
        """Capture frame and update display"""
        if not self.timer.is_timedout():
            return False
        
        self.timer.reset(self._rtsp.refresh_time)
        # Get frame from RTSP stream
        self.frame = self.grabber.get_frame_pil()
        if self.frame is None:
            print(f"Failed to capture frame from {self.url}")
            self._reconnect()
            return False
        return True
    
    def cleanup(self):
        """Cleanup on module shutdown"""
        self.grabber.disconnect()
