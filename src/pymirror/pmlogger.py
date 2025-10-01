import enum
import inspect
import functools
import os
from textwrap import wrap
global pmlogger, _debug, _info, _warning, _error, _critical, _trace, _enter, _exit, _print

_print = print

def trace_method(func):
    """Decorator to trace individual methods"""
    # check func is already traced
    if hasattr(func, '_is_traced_'): return func
    print("xxx", func)
    setattr(func, '_is_traced_', True)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Mark the function as traced
        # Get function name and class name if it's a method
        func_name = func.__name__
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            full_name = f"{class_name}.{func_name}"
        else:
            full_name = func_name
        cwd = os.getcwd()
        # get the file name (removing cwd) and line number
        frame = inspect.currentframe().f_back
        file_name = frame.f_code.co_filename
        file_name = file_name.replace(cwd, ".")
        line_number = frame.f_lineno
        # Enter the function
        pmlogger._trace_enter(full_name, f"({file_name}:{line_number})")

        try:
            result = func(*args, **kwargs)
            pmlogger._trace_exit("->", type(result))
            return result
        except Exception as e:
            pmlogger._trace_exit("-> EXCEPTION:", str(e))
            raise
    setattr(wrapper, '_is_traced_', True)
    return wrapper

def trace(cls):
    """Class decorator to automatically trace all methods"""
    # check if cls is a method
    if inspect.isfunction(cls) or inspect.ismethod(cls):
        return trace_method(cls)

    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        # Only wrap callable methods, skip special methods and properties
        if (callable(attr) and 
            not attr_name.startswith('__') and 
            not isinstance(attr, (property, staticmethod, classmethod))
            ):
            
            # Apply the METHOD trace decorator (not the class decorator)
            traced_method = trace_method(attr)
            setattr(cls, attr_name, traced_method)
    
    return cls

class PMLoggerLevel(enum.Enum):
    INFO = 1
    DEBUG = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5
    NONE = 6

class PMLogger:
    # class variable to hold the logger instance
    c_level = None
    c_fn_stack = [""]
    c_trace = True

    def __init__(self, log_file=None, level=PMLoggerLevel.WARNING):
        self.log_file = log_file
        self.c_level = level

    def set_level(self, level: PMLoggerLevel):
        """Set the logging level."""
        self.c_level = level
        self.debug(f"Logging level set to: {level.name}")

    def set_trace(self, trace: bool):
        """Set the tracing flag."""
        self.c_trace = trace
        self.debug(f"Tracing set to: {trace}")

    def set_global_level(self, level: PMLoggerLevel):
        """Set the logging level."""
        PMLogger.c_level = level
        self.debug(f"Logging level set to: {level.name}")

    def get_level(self):
        """Get the current logging level."""
        return PMLogger.c_level or self.c_level

    def _print(self, level: str, fn: str, message: str, indent_str: str = "|  "):
        # Print the message with indentation based on the current level
        indent = indent_str * (len(PMLogger.c_fn_stack) - 1)
        print(f"{indent}{(level + ': ') if level else ''}{message}")

    def _trace(self, *args):
        if self.c_trace:
            indent = "|  " * (len(PMLogger.c_fn_stack) - 1)
            print(f"{indent}{' '.join(map(str, args))}")

    def _trace_enter(self, function_name, *args):
        if self.c_trace:
            self._trace(f">{function_name}", *args)
            PMLogger.c_fn_stack.append(function_name)

    def _trace_exit(self, *args):
        if self.c_trace:
            function_name = PMLogger.c_fn_stack.pop()
            self._trace(f"<{function_name}", *args)

    def trace(self, *args):
        frame = inspect.currentframe().f_back
        function_name = (PMLogger.c_fn_stack[-1].split(".")[-1] if PMLogger.c_fn_stack else "unknown")
        is_traced = frame.f_code.co_name == function_name
        if is_traced:
            self._trace(*args)

    def log(self, level, *args):
        if level.value >= self.get_level().value:
            self._print(level=level.name, fn=PMLogger.c_fn_stack[-1], message=" ".join(map(str, args)))

    def debug(self, *args):
        self.log(PMLoggerLevel.DEBUG, *args)

    def info(self, *args):
        self.log(PMLoggerLevel.INFO, *args)

    def warning(self, *args):
        self.log(PMLoggerLevel.WARNING, *args)

    def error(self, *args):
        self.log(PMLoggerLevel.ERROR, *args)

    def critical(self, *args):
        self.log(PMLoggerLevel.CRITICAL, *args)

pmlogger = PMLogger()
_debug = pmlogger.debug
_info = pmlogger.info
_warning = pmlogger.warning
_error = pmlogger.error
_critical = pmlogger.critical
_trace = pmlogger.trace

if __name__ == "__main__":

    @trace
    class TestLogger:
        def bar(self, msg=""):
            _info("This is an info message.")
            _warning("This is a warning message.")
            _trace("Tracing bar...")
            _debug("this", "is", "a", "debug", "message")
            _error("This is an error message.")
            return {
                "msg": msg,
                "status": "ok",
                "code": 200,
                "data": {"key": "value"},
            }
        def foo(self, flibbitz=""):
            _info("This is an info message.")
            _trace("Tracing foo...")
            _debug("this", "is", "a", "debug", "message")
            self.bar()
            _warning("This is a warning message.")
            _error("This is an error message.")
    
    def main():
        pmlogger.set_level(PMLoggerLevel.NONE)
        pmlogger.set_trace(True)
        test_logger = TestLogger()
        _info("This is an info message.")
        _warning("This is a warning message.")
        _debug("this", "is", "a", "debug", "message")

        test_logger.foo("flibbitz")
        _error("This is an error message.")
        _critical("This is a critical message.")

if __name__ == "__main__":
    main()