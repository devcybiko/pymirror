import json5
import json
from glslib.logger import _print
from dataclasses import is_dataclass

def json_read(fname: str, dflt=None) -> dict:
    with open(fname, 'r') as file:
        s = file.read()
        return json_loads(s)

def json_write(fname: str, obj: dict) -> bool:
    with open(fname, 'w') as file:
        file.write(json_loads(obj))
        return 

def json_loads(s: str, dflt=None) -> dict:
    # try:
        return json5.loads(s)
    # except Exception as e:
    #     err_msg = str(e)
    #     words = err_msg.split(" ")
    #     line_no = int(words[0].split(":")[1])-1
    #     col = int(words[5])-1
    #     lines = s.split("\n")
    #     ptr = ("." * col) + "^"
    #     raise ValueError(f"{err_msg}\n{line_no-1}:{lines[line_no-1]}\n{line_no}:{lines[line_no]}\n{line_no}:{ptr}\n{line_no+1}:{lines[line_no+1]}")

def json_dumps(d: dict, dflt=None, indent=2) -> str:
    def default_handler(obj):
        # Try to serialize dataclasses, objects with __dict__, or fallback to str
        if is_dataclass(obj):
            return obj.__dict__
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        if hasattr(obj, '__str__'):
            return str(obj)
        return f"<non-serializable: {type(obj).__name__}>"
    try:
        return json.dumps(d, indent=indent, default=default_handler)
    except Exception as e:
        _print(e)
        # raise e
        return dflt
