import sys
import httpx
import asyncio
import json
import time
import inspect

from pymirror.pmlogger import _debug, _debug, _error, trace, _trace, _debug, _warning
from pymirror.utils.utils import SafeNamespace, to_ms
from pymirror.pmlogger import pmlogger, PMLoggerLevel
from pymirror.pmcaches import FileCache, MemoryCache, MemoryFileCache

# pmlogger.set_level(PMLoggerLevel.WARNING)

class PMWebApi:
    def __init__(self, url: str, poll_time: str = "1h", cache_file: str = None):
        self.url = url
        ##
        self.async_loop = asyncio.get_event_loop()
        self.task = None
        print("webapi:", url, poll_time, cache_file)
        self.file_cache = MemoryFileCache(text=None, fname=cache_file, timeout_ms=to_ms(poll_time)) if cache_file else None
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
            return self._fetch_response_blocking(blocking) \
                or self._fetch_response_non_blocking(blocking)
        except Exception as e:
            self.cancel()
            self.error = e
    
    def fetch_text(self, blocking=True):
        if self.task:
            ## we're waiting on a spawned httpx task
            if blocking:
                # wait until the task is complete
                self.async_loop.run_until_complete(self.task)
            else:
                # wait a 'tick' to let the underlying event engine run
                self.async_loop.run_until_complete(asyncio.sleep(self.async_delay))
            if self.task.done():
                # if the task is done (either because it completed, timed out, or was blocked)
                self.response = self.task.result()
                self.text = self.response.text
                self.file_cache.set(self.text)
                self.cancel()
            else:
                self.text = self.file_cache.get()
        else:
            # the task was never started or it completed
            # get the file_cache
            self.text = self.file_cache.get()
            if self.text == None:
                self.start()
                # call fetch_text() recursively to wait for the task to complete
                # or return the cached value
                return self.fetch_text(blocking)
        return self.text

    def fetch_json(self, blocking=True):
        result = None
        try:
            _debug(f"Fetching json from {self.url}...")
            text = self.fetch_text(blocking=blocking)
            if text:
                result = json.loads(text)
        except Exception as e:
            self.error = e
        return result

    def _fetch_response_blocking(self, blocking):
        if not blocking:
            return None
        _debug(f"Blocking fetch from {self.url} with method {self.httpx.method}")
        self.start()
        self.async_loop.run_until_complete(self.task)
        result = self.task.result()
        self.error = None ## GLS - resetting error (set because file not found or out of date)
        self.cancel()
        return result

    def _fetch_response_non_blocking(self, blocking):
        if blocking:
            return None
        _debug(f"Non-blocking fetch from {self.url} with method {self.httpx.method}")
        if self.task is None:
            self.start()
        self.async_loop.run_until_complete(asyncio.sleep(self.async_delay))
        if not self.task.done():
            _debug(f"Fetch task NOT completed for {self.url}")
            self.error = None
            return None
        _debug(f"Fetch task completed for {self.url}")
        response = self.task.result()
        self.cancel()
        return response

    def _fetch_text_from_api(self, blocking=True):
        text = None
        self.error = None
        response = self.fetch(blocking=blocking)
        _debug(f"Fetch response from {self.url}: {response}")
        if not response:
            return None
        _debug(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            text = response.text
        else:
            self.error = Exception(f"HTTP {response.status_code}: {response.text}")
        return text
    
    async def _async_fetch(self):
        async with httpx.AsyncClient(timeout=self.httpx.timeout_secs) as client:
            method = self.httpx.method.upper()
            _debug(f"Fetching {self.url} with method {method}...")
            # Select the method dynamically
            _debug(f"...headers: {self.httpx.headers}, params: {self.httpx.params}")
            response = await client.request(
                method,
                self.url,
                headers=self.httpx.headers,
                params=self.httpx.params,
                data=self.httpx.data if method != "GET" else None,
                json=self.httpx.json if method != "GET" else None,
                follow_redirects=True
            )
            _debug(f"Received response from {self.url} with status code {response.status_code}")
            return response

def main():
    import dotenv
    dotenv.load_dotenv('.secrets')
    api = PMWebApi("https://httpbin.org/delay/1", poll_time="10s", cache_file='./caches/test.json')

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