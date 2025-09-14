from datetime import datetime
import sys
import httpx
import asyncio
import json
import time
import inspect

from pymirror.pmlogger import _debug, _debug, _error, trace, _trace, _debug, _warning
from pymirror.utils import SafeNamespace, json_loads, to_ms
from pymirror.pmlogger import pmlogger, PMLoggerLevel
from pymirror.pmcaches import FileCache, MemoryCache, MemoryFileCache

# pmlogger.set_level(PMLoggerLevel.WARNING)

class PMWebApi:
    def __init__(self, url: str, poll_time: str = "1h", cache_file: str = None):
        self.url = url
        ##
        self.async_loop = asyncio.get_event_loop()
        self.task = None
        _debug("webapi:", url, poll_time, cache_file)
        self._async_delay = 0.001
        self._httpx = self.set_httpx()
        self.response = None # last valid response
        self.response_time = None # time of last valid response
        self.error = None # last error

    def set_httpx(self, method="get", headers={"Accept": "application/json"}, params={}, data=None, json=None, timeout_time="5s"):
        httpx = SafeNamespace()
        httpx.method = method
        httpx.headers = headers
        httpx.params = params
        httpx.data = data
        httpx.json = json
        httpx.timeout_secs = to_ms(timeout_time) * 1000
        return httpx

    def start(self): 
        self.error = None
        self.task = self.async_loop.create_task(self._async_fetch())

    def cancel(self):
        if self.task:
            self.task.cancel()
            self.task = None

    def reset(self):
        self.cancel()
        self.response = None
        self.response_time = None
        self.error = None

    def fetch(self, blocking=True):
        try:
            if self.task == None:
                self.start()
            if blocking:
                # wait for the task to finish
                self.async_loop.run_until_complete(self.task)
            else:
                # give the task loop time to process
                self.async_loop.run_until_complete(asyncio.sleep(self._async_delay))
            if self.task.done():
                # we got a result
                self.response = self.task.result()
                self.response_time = datetime.now()
                self.cancel()
                result = self.response
        except Exception as e:
            self.error = e
            self.cancel()
        return self.response
    
    def fetch_text(self, blocking=True):
        result = None
        response = self.fetch(blocking)
        if response:
            result = response.text
        return result

    def fetch_json(self, blocking=True):
        result = None
        text = self.fetch_text(blocking=blocking)
        if text:
            result = json_loads(text)
        return result
    
    async def _async_fetch(self):
        async with httpx.AsyncClient(timeout=self._httpx.timeout_secs) as client:
            method = self._httpx.method.upper()
            _debug(f"Fetching {self.url} with method {method}...")
            # Select the method dynamically
            _debug(f"...headers: {self._httpx.headers}, params: {self._httpx.params}")
            response = await client.request(
                method,
                self.url,
                headers=self._httpx.headers,
                params=self._httpx.params,
                data=self._httpx.data if method != "GET" else None,
                json=self._httpx.json if method != "GET" else None,
                follow_redirects=True
            )
            _debug(f"Received response from {self.url} with status code {response.status_code}")
            return response

def main():
    import dotenv
    dotenv.load_dotenv('.secrets')
    api = PMWebApi("https://httpbin.org/delay/2", poll_time="10s", cache_file='./caches/test.json')

    result = None
    print("initiate the api call...")
    while result is None:
        print("...")
        result = api.fetch_json(blocking=False)
        if api.error:
            _error(f"first loop: Error fetching json from {api.url}:\n{repr(api.error)}")
            sys.exit(1)
        time.sleep(0.1)
    print("result", result)
    print("end of first loop...")

    result = None
    while result is None:
        print("...")
        result = api.fetch_json(blocking=False)
        if api.error:
            _error(f"second loop: Error fetching json from {api.url}:\n{repr(api.error)}")
            sys.exit(1)
        time.sleep(0.1)
    print("result", result)
    print("end of second loop...")
    api.reset()
    print("... reset()")

    result = None
    while result is None:
        print("...")
        result = api.fetch_json(blocking=False)
        if api.error:
            _error(f"second loop: Error fetching json from {api.url}:\n{repr(api.error)}")
            sys.exit(1)
        time.sleep(0.1)
    print("result", result)
    print("end of third loop...")

if __name__ == "__main__":
    main()