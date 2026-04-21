"""
RTSP Frame Grabber using PyAV (ffmpeg library bindings)
No subprocess overhead - direct C library calls
Returns PIL Images for real-time use in applications
"""
from pathlib import Path
import threading
import av
from av import container
from httpx import stream
from urllib.parse import quote

class PyAVRTSPGrabber:
    """Grab RTSP frames using PyAV (ffmpeg library bindings)"""
    
    def __init__(self, rtsp_url: str, timeout: int = 5):
        if av is None:
            raise ImportError("PyAV not installed. Install with: pip install av")
        
        # URL-encode credentials to handle special characters
        self.rtsp_url = self._encode_url(rtsp_url)
        self.latest_frame = None
        self.stopped = False
        self.thread = None
        self.codec = None
        # Parse timeout - can be string like "5s" or int
        if isinstance(timeout, str):
            timeout = int(timeout.rstrip('s'))
        self.timeout = timeout
        
        self.container = None
        # FFmpeg options for RTSP
        self.open_options = {
            'rtsp_transport': 'tcp',
            'probesize': '32',
            'analyzeduration': '0',
            'fflags': 'nobuffer',
            # 'rw_timeout': str(self.timeout * 1000000),
        }
    
    def _encode_url(self, url: str) -> str:
        """URL-encode credentials in RTSP URL"""
        if '://' not in url or '@' not in url:
            return url
        
        scheme, rest = url.split('://', 1)
        credentials, host_path = rest.rsplit('@', 1)
        
        if ':' not in credentials:
            return url
        
        user, password = credentials.split(':', 1)
        # URL encode special characters in password and username
        encoded_user = quote(user, safe='')
        encoded_password = quote(password, safe='')
        
        return f"{scheme}://{encoded_user}:{encoded_password}@{host_path}"
    
    def _connect(self) -> bool:
        try:
            if self.container is None:
                print(f"Opening RTSP stream: {self.rtsp_url}")
                self.container = av.open(self.rtsp_url, options=self.open_options)
                stream = self.container.streams.video[0]
                self.codec = av.CodecContext.create(stream.codec_context.name, "r")
                print("RTSP stream opened")
            return True
        except Exception as e:
            print(f"Error connecting to RTSP: {e}")
            self.container = None
            return False

    def _reader(self):
        """Background thread to constantly clear the buffer"""
        try:
            # container = av.open(self.rtsp_url, options=self.open_options)
            stream = self.container.streams.video[0]
            self.codec = av.CodecContext.create(stream.codec_context.name, "r")
            for packet in self.container.demux(stream):
                if self.stopped:
                    break
                    
                # If the packet is a "Keyframe" (I-Frame), we might want it
                # This is the secret: we only decode when we actually NEED a frame
                # OR we decode at a much lower frequency than 30fps
                if packet.is_keyframe:
                    frames = self.codec.decode(packet)
                    if frames:
                        self.latest_frame = frames[-1]
                
                # Packets that aren't keyframes are ignored/discarded 
                # with almost zero CPU cost.
        except Exception as e:
            print(f"Stream error: {e}")

    def _reader_demux(self):
        """
        Background thread to constantly read and demux packets.
        This is less CPU intensive but may introduce more latency.
        It only returns the 'I'-Frames (keyframes) which are the most important for real-time display.
        Frame rate is determined by the stream's keyframe interval, which is often 1-4 seconds for RTSP cameras.
        """

        try:
            # container = av.open(self.rtsp_url, options=self.open_options)
            stream = self.container.streams.video[0]
            self.codec = av.CodecContext.create(stream.codec_context.name, "r")
            for packet in self.container.demux(stream):
                if self.stopped:
                    break
                    
                # If the packet is a "Keyframe" (I-Frame), we might want it
                # This is the secret: we only decode when we actually NEED a frame
                # OR we decode at a much lower frequency than 30fps
                if packet.is_keyframe:
                    frames = self.codec.decode(packet)
                    if frames:
                        self.latest_frame = frames[-1]
        except Exception as e:
            print(f"Stream error: {e}")

    def _reader_decode(self):
        """
        Background thread to constantly read and decode frames.
        This is more CPU intensive but ensures you get the latest frame."""
        try:
            # container = av.open(self.rtsp_url, options=self.options)
            stream = self.container.streams.video[0]
            for frame in self.container.decode(stream):
                if self.stopped:
                    break
                self.latest_frame = frame
        except Exception as e:
            print(f"Stream interrupted: {e}. Retrying in 2s...")
            import time
            time.sleep(2)

    def start(self):
        self.stopped = False
        ### choose the one that is most performant for your use case:
        self.thread = threading.Thread(target=self._reader_decode, daemon=True)
        # self.thread = threading.Thread(target=self._reader_demux, daemon=True)
        self.thread.start()

    def get_frame_pil(self):
        if not self._connect():
            return None

        if not self.thread or not self.thread.is_alive():
            self.start()
            
        if self.latest_frame:
            # Optional: Clear the frame after reading to ensure 
            # you don't process the same frame twice if the stream lags
            return self.latest_frame.to_image()
        return None

    def stop(self):
        self.stopped = True

    def save_frame(self, output_path: str) -> bool:
        try:
            img = self.get_frame_pil()
            if img is None:
                return False
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, quality=85)
            
            return True
        except Exception as e:
            print(f"Error saving frame: {e}")
            return False
    
    def disconnect(self):
        if self.container is not None:
            self.container.close()
            self.container = None
    
    def __del__(self):
        self.disconnect()