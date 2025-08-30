import sys
import httpx
import asyncio
import json
import time
import inspect

from pymirror.pmlogger import _print, _print, _error, trace
from pymirror.utils import SafeNamespace
from pymirror.pmlogger import pmlogger, PMLoggerLevel
from pymirror.pmcaches import FileCache, MemoryCache

# pmlogger.set_level(PMLoggerLevel.DEBUG)

# @trace
class PMWebApi:
    def __init__(self, url: str, poll_secs: int = 3600, cache_file: str = None):
        self.url = url
        self.poll_secs = poll_secs
        ##
        self.async_loop = asyncio.get_event_loop()
        self.task = None
        self.memory_cache = MemoryCache(text=None, timeout_ms=poll_secs * 1000)
        self.file_cache = FileCache(text=None, fname=cache_file, timeout_ms=poll_secs * 1000) if cache_file else None
        self.async_delay = 0.01
        self.httpx = self.set_httpx()
        self.error = None
        self.from_cache = False
        self.text = None

    def set_httpx(self, method="get", headers={"Accept": "application/json"}, params={}, data=None, json=None, timeout_secs=5):
        httpx = SafeNamespace()
        httpx.method = method
        httpx.headers = headers
        httpx.params = params
        httpx.data = data
        httpx.json = json
        httpx.timeout_secs = timeout_secs
        return httpx

    @property
    def last_date(self):
        return self.file_cache.file_info.last_date 

    def is_from_cache(self):
        return self.from_cache

    def start(self): 
        self.task = self.async_loop.create_task(self._async_fetch())

    def cancel(self):
        if self.task:
            self.task.cancel()
            self.task = None

    def fetch(self, blocking=True):
        try:
            return self._fetch_blocking(blocking) \
                or self._fetch_non_blocking(blocking)
        except Exception as e:
            self.cancel()
            self.error = e

    def _get_memory_cache(self):
        cached_text = self.memory_cache.get()
        if cached_text:
            _print(" | Cached memory is valid")
            self.from_cache = False
        return cached_text
    
    def _get_file_cache(self):
        if not self.file_cache:
            return None
        cached_text = self.file_cache.get()
        if cached_text:
            _print(f" | Cached file {self.file_cache.file_info.fname} is valid")
            self.from_cache = True
        else:
            _print(f" | Cached file {self.file_cache.file_info.fname} is invalid / timed out")
        return cached_text

    def _get_api_text(self, blocking):
        api_text = self._fetch_from_api(blocking)
        if api_text != None:
            _print(f" |  | API response from {self.url} is non-null")
            self.from_cache = False
            ## update the cache if the text has changed
            self.memory_cache.update(api_text)
            self.file_cache.update(api_text)
            return api_text
        ## api returned nothing - error or non-blocking read
        _print(f" |  | API response from {self.url} is null (non-blocking or error)")
        if self.error:
            _error(f"Error fetching API response from {self.url}: {self.error}")
            self.from_cache = False
            return None

    def fetch_text(self, blocking=True):
        self.text = (
            self._get_memory_cache()
            or self._get_file_cache()
            or self._get_api_text(blocking)
        )
        return self.text

    def fetch_json(self, blocking=True):
        result = None
        try:
            _print(f"Fetching json from {self.url}...")
            text = self.fetch_text(blocking=blocking)
            if text:
                result = json.loads(text)
        except Exception as e:
            self.error = e
        return result

    def _fetch_blocking(self, blocking):
        if not blocking:
            return None
        _print(f"Blocking fetch from {self.url} with method {self.httpx.method}")
        self.start()
        self.async_loop.run_until_complete(self.task)
        result = self.task.result()
        self.error = None ## GLS - resetting error (set because file not found or out of date)
        self.cancel()
        return result

    def _fetch_non_blocking(self, blocking):
        if blocking:
            return None
        _print(f"Non-blocking fetch from {self.url} with method {self.httpx.method}")
        if self.task is None:
            self.start()
        ## give asyncio some time to process
        self.async_loop.run_until_complete(asyncio.sleep(self.async_delay))
        if not self.task.done():
            _print(f"Fetch task NOT completed for {self.url}")
            self.error = None ## GLS - resetting error (set because file not found or out of date)
            return None
        _print(f"Fetch task completed for {self.url}")
        result = self.task.result()
        self.cancel()
        return result

    def _fetch_from_api(self, blocking=True):
        text = None
        self.error = None
        response = self.fetch(blocking=blocking)
        _print(f"Fetch response from {self.url}: {response}")
        if not response:
            return None
        _print(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            text = response.text
        else:
            self.error = Exception(f"HTTP {response.status_code}: {response.text}")
        return text
    
    async def _async_fetch(self):
        async with httpx.AsyncClient(timeout=self.httpx.timeout_secs) as client:
            method = self.httpx.method.upper()
            _print(f"Fetching {self.url} with method {method}...")
            # Select the method dynamically
            _print(f"...headers: {self.httpx.headers}, params: {self.httpx.params}")
            response = await client.request(
                method,
                self.url,
                headers=self.httpx.headers,
                params=self.httpx.params,
                data=self.httpx.data if method != "GET" else None,
                json=self.httpx.json if method != "GET" else None,
                follow_redirects=True
            )
            _print(f"Received response from {self.url} with status code {response.status_code}")
            return response

def main():
    import dotenv
    dotenv.load_dotenv('.secrets')
    api = PMWebApi("https://httpbin.org/delay/1", poll_secs=10, cache_file='./caches/test.json')

    result = None
    print("initiate the api call...")
    while result is None:
        result = api.fetch_json(blocking=True)
        if api.error:
            _error(f"first loop: Error fetching json from {api.url}:\n{repr(api.error)}")
            sys.exit(1)
        time.sleep(0.1)
    print(f"Response {len(result or '')} is {'not ' if not api.from_cache else ''}from cache")
    while api.is_from_cache():
        result = api.fetch_json(blocking=True)
        if api.error:
            _error(f"second loop: Error fetching json from {api.url}:\n{repr(api.error)}")
            sys.exit(1)
        print(f"... from cache: {len(result or '')} self.file_cache: {time.ctime(time.time())}, {api.file_cache.file_info.last_date}")
        time.sleep(1.0)
    print("result", result)
    print(f"Response is {'not ' if not api.from_cache else ''}from cache")
if __name__ == "__main__":
    main()