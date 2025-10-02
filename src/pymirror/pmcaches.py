import os
from pydoc import text
import sys
import time
from abc import ABC, abstractmethod

from pymirror.pmtimer import PMTimer
from pymirror.pmlogger import _debug, _error, _debug, pmlogger, PMLoggerLevel, trace, _trace

# pmlogger.set_level(PMLoggerLevel.WARNING)

class FileInfo:
    def __init__(self, fname=None, create=True):
        self.fname = fname
        self.exists = False
        self.error = None
        self.size = 0
        self.last_modified = 0
        self.last_date = None
        self.error = None
        if create:
             open(self.fname, "a").close()
        if not os.path.exists(self.fname):
            _error(f"File does not exist: {self.fname}")
            raise Exception(f"file not readable {self.fname}")
        self.update_stats()

    def reset(self):
        self.exists = False
        self.error = None
        self.size = 0
        self.last_modified = 0
        self.last_date = None

    def update_stats(self):
        """ Update file info and return True if readable, False otherwise."""
        _debug(f"checking readability of {self.fname}")
        self.reset()
        self.exists = os.path.exists(self.fname)
        if self.exists:
            self.size = os.path.getsize(self.fname)
            self.last_modified = os.path.getmtime(self.fname)
            self.last_date = time.ctime(self.last_modified)
            return self.size > 0 # GLS - may be a problem - are empty files readable?
        self.error = Exception(f"file not readable {self.fname}")
        return False
    
    def is_expired(self, timeout_ms):
        if not self.exists:
            _debug(f"file {self.fname} does not exist, so is expired")
            return True
        now = time.time()
        last_modified = self.last_modified + timeout_ms / 1000
        _debug(f"checking expiry of {self.fname}: expired={last_modified <= now}, now={now}, last_modified+timeout={last_modified}")
        return last_modified <= now

    def save(self, text) -> bool:
        """ Save the text, and return True if successful, False otherwise."""
        try:
            self.error = None
            with open(self.fname, 'w') as file:
                _debug(f"Saving cache to {self.fname} with {len(text or '')}")
                file.write(text or "")
            return True
        except Exception as e:
            _error(f"Error saving cache: {e}")  # Add this for debugging
            self.error = e
            return False

    def read(self) -> str | None:
        """ Read the text from the file, and return it or None if failed."""
        try:
            self.error = None
            with open(self.fname, 'r') as file:
                text = file.read()
                if len(text or '') == 0:
                    _debug(f"Read cache from {self.fname}: empty")
                    text = None
                _debug(f"Read cache from {self.fname}: '{text}'")
                return text
        except Exception as e:
            self.error = e
            _print(f"Error reading cache {self.fname}: {e}")
            return None

class Cache(ABC):
    def __init__(self):
        self.type = None
        self.text = None

    @abstractmethod
    def set(self, text): ...

    @abstractmethod
    def invalidate(self): ...

    @abstractmethod
    def get(self): ...

    @abstractmethod
    def update(self, text): ...

class MemoryFileCache(Cache):
    def __init__(self, text=None, timeout_ms=1000, fname=None):
        _print("MemoryFileCache()", text, timeout_ms, fname)
        self.memory_cache = MemoryCache(text, timeout_ms / 2)
        self.file_cache = FileCache(text=text, fname=fname, timeout_ms=timeout_ms)
        self.file_info = self.file_cache.file_info
    
    def set(self, text):
        self.memory_cache.set(text)
        self.file_cache.set(text)
    
    def update(self, text):
        if text != self.text:
            self.set(text)

    def invalidate(self):
        self.memory_cache.invalidate()
        self.file_cache.invalidate()

    def get(self):
        text = self.memory_cache.get()
        if not text:
            text = self.file_cache.get()
        return text

    def read(self):
        return self.file_cache.read()

class MemoryCache(Cache):
    def __init__(self, text=None, timeout_ms=1000):
        self.timer = PMTimer(timeout_ms)
        self.set(text)

    def set(self, text):
        self.text = text
        self.timer.reset()

    def update(self, text):
        if text != self.text:
            self.set(text)

    def invalidate(self):
        self.text = None
        self.timer.set_timeout(0)
    
    def get(self):
        _trace("... get()")
        is_timedout = self.timer.is_timedout()
        _trace("... is_timedout", is_timedout)
        if is_timedout:
            _trace("... invalidating")
            self.invalidate()
        _trace("... returning->", self.text)
        return self.text

class FileCache(Cache):
    def __init__(self, text=None, timeout_ms=1000, fname=None):
        _print("FileCache()", fname)
        self.file_info = FileInfo(fname)
        self.timeout_ms = timeout_ms
        self.text = text

    def update(self, text):
        ## write the cache only if it's changed
        if text != self.text:
            _debug(f"text != self.text")
            _debug(f" | text: {text}")
            _debug(f" | self.text: {self.text}")
            self.set(text)

    def set(self, text):
        self.text = text
        _debug(f"File cache {self.file_info.fname} set to: {len(text or '')}")
        self.file_info.save(text or "")
        self.error = self.file_info.error
        if self.error:
            self.invalidate()

    def invalidate(self):
        _debug(f"Invalidating file cache {self.file_info.fname}")
        self.text = None

    def read(self):
        self.file_info.update_stats()
        return self.file_info.read()

    def get(self):
        """ if the cached file is not expired, return its content """
        _debug(f"Getting file cache {self.file_info.fname}")
        if self.text == None:
            ## the cache is invalid
            if not self.file_info.is_expired(self.timeout_ms):
                # the cache file is still valid
                _debug(f"file not expired... Loading cache from file {self.file_info.fname}")
                self.text = self.file_info.read()
            else:
                _debug(f"file expired... invalidating {self.file_info.fname}")
                # the cache is still invalid
                self.invalidate()
        else:
            # the cache is valid, but...
            if self.file_info.is_expired(self.timeout_ms):
                # invalidate the cache
                _debug(f"valid cache, but file expired... invalidating {self.file_info.fname}")
                self.invalidate()
        self.error = self.file_info.error
        return self.text

if __name__ == "__main__":
    def memtest():
        memcache = MemoryCache("one second later", 1000)
        while memcache.get():
            _print(f"Memory cache: {memcache.get()}")
            time.sleep(0.2)
        memcache = MemoryCache("two seconds later", 1000)
        for i in range(2):
            _print(f"Memory cache: {memcache.get()}")
            time.sleep(0.2)
        memcache.invalidate()
        while memcache.get():
            _print(f"Memory cache: {memcache.get()}")
            time.sleep(0.2)
        memcache.update("testing update")
        _print(f"Memory cache: {memcache.get()}")
        time.sleep(0.2)
        if memcache.get() != "testing update":
            _print(f"Memory cache error: value should not have changed")
        memcache.update("testing update w/ change")
        while memcache.get():
            _print(f"Memory cache: {memcache.get()}")
            time.sleep(0.2)

    def filetest():
        # filecache = FileCache("", 2000, "caches/test_cache.txt")
        # while filecache.get():
        #     _print(f"File cache {filecache.file_info.fname}: {filecache.get()}")
        #     time.sleep(0.2)
        # _print(f"File cache error: {filecache.error}")
        # filecache.set("new file cache test")
        # for i in range(2):
        #     _print(f"File cache {filecache.file_info.fname}: {filecache.get()}")
        #     time.sleep(0.2)
        # _print(f"File cache error: {filecache.error}")
        # filecache.set("third file cache test")
        # while filecache.get():
        #     _print(f"File cache {filecache.file_info.fname}: {filecache.get()}")
        #     time.sleep(0.2)
        # _print(f"File cache error: {filecache.error}")
        
        # filecache = FileCache("file cache test", 2000, "/bad_file_name.txt")
        # while filecache.get():
        #     _print(f"File cache {filecache.file_info.fname}: {filecache.get()}")
        #     time.sleep(0.2)
        # _print(f"File cache error: {filecache.error}")

        filecache = FileCache("testing update w/ no change", 1000, "caches/test_cache.txt")
        for i in range(2):
            _print(f"File cache {filecache.file_info.fname}: {filecache.get()}")
            time.sleep(0.2)
        _print(f"File cache error: {filecache.error}")
        filecache.update("testing update w/ no change")
        while filecache.get():
            _print(f"File cache {filecache.file_info.fname}: {filecache.get()}")
            time.sleep(0.2)
        filecache.set("new file cache test")
        _print(f"File cache error: {filecache.error}")

        filecache = FileCache("testing update w/ change", 1000, "caches/test_cache.txt")
        for i in range(2):
            _print(f"File cache {filecache.file_info.fname}: {filecache.get()}")
            time.sleep(0.2)
        _print(f"File cache error: {filecache.error}")
        filecache.update("testing update with a change")
        while filecache.get():
            _print(f"File cache {filecache.file_info.fname}: {filecache.get()}")
            time.sleep(0.2)
        _print(f"File cache error: {filecache.error}")

    memtest()
    filetest()