from dataclasses import fields as dc_fields
import importlib
from typing import get_type_hints
from utils.utils import json_dumps, json_loads, json_read, pascal_to_snake, snake_to_pascal, to_dict
from pmlogger import trace, trace_method, _trace, _info, _print, _warning

class Object:
    def __init__(self):
        pass

@trace
class PMConfig:
    """
    NOTE: Also used as a "marker" for instantiated Configs

    Pulls in "configs" from json or dicts.
    Configs are dataclasses which gives us strong type checking
    The configs are defined in the current package
    And they are expected to include default values.
    """
    def __init__(self):
        pass

    def _handle_strict_types(self, clazz, obj: any):
        """Validate and convert types after initialization"""
        type_hints = get_type_hints(clazz)
        for field_name, _expected_type in type_hints.items():
            ## if it's a subclass of some other class... get its super class
            expected_type = getattr(_expected_type, '__origin__', _expected_type)
            ## for each field and its expected type...
            if hasattr(obj, field_name):
                _info("... object does not have field", field_name, "...skipping...")
                continue
            ## get the value from the object
            value = getattr(obj, field_name)
            if value == None:
                _warning("... object does not have a VALUE for field", field_name, "...skipping...")
                continue
            if isinstance(value, dict):
                ## its a dictionary just assign it to the object
                setattr(obj, field_name, value)
            elif not isinstance(value, expected_type):
                try:
                    # Try to convert the type
                    converted_value = expected_type(value)
                    setattr(obj, field_name, converted_value)
                except (ValueError, TypeError) as e:
                    raise TypeError(f"Field '{clazz.__name__}.{field_name}' expected {expected_type.__name__}, got {type(value).__name__}: {value}")
    @trace_method
    def _handle_fields(self, clazz, values):
        ## get all the field names from the clazz
        field_names = {f.name for f in dc_fields(clazz)}

        ## extract all the items from the "values" that are fields in the dataclass
        ## if the value isn't named it will be "attached" as an attribute late
        ## if a field_name doesn't have a matching value, then the new obj will use the default
        ## if a field_name doesn't have a default value and the "values" doesnt offer one,
        ## and exception will be thrown when `obj = clazz(**valid_values)`
        valid_values = {k: v for k, v in values.items() if k in field_names}

        ## create the object with the values that were passed in
        ## NOTE: default values won't fail but required values will
        obj = clazz(**valid_values)

        # Attach any unnamed fields as attributes
        for k, v in values.items():
            if k not in field_names:
                setattr(obj, k, v)
        return obj

    def _handle_lists(self, field_type, field_name, obj):
        obj_value = getattr(obj, field_name)
        origin = getattr(field_type, "__origin__", None)
        args = getattr(field_type, "__args__", None)
        if origin is list and args:
            list_item_type = args[0]  # AlertConfig
            if isinstance(obj_value, list):
                # Process each item in the list as a config
                processed_items = []
                for item in obj_value:
                    if isinstance(item, dict):
                        # Convert dict to AlertConfig
                        config_name = list_item_type.__name__.lower().replace('config', '')
                        nested_config = self._load_config(config_name, item)
                        processed_items.append(nested_config)
                    else:
                        processed_items.append(item)
                setattr(obj, field_name, processed_items)

    def _handle_dicts(self, clazz, obj):
        ## iterate over all the fields of the obj converting dicts to *Configs
        type_hints = get_type_hints(clazz)
        for field in dc_fields(obj):
            field_name = field.name
            field_type = type_hints.get(field_name)
            obj_value = getattr(obj, field_name)
            # Check if field value is a dict that should be converted to a config
            if isinstance(obj_value, dict) and field_type != dict:
                # Convert dict to config recursively
                if field_type.__name__.endswith("Config"):
                    ## crude way to determine, but...
                    clazz_name = pascal_to_snake(field_type.__name__)
                    nested_config = self._load_config(clazz_name.replace('_config', ''), obj_value)
                    if nested_config != None:
                        ## None means config was "commented out" with "_config_name"
                        setattr(obj, field_name, nested_config)
                else:
                    nested_config = self._load_config(field_name, obj_value)
                    if nested_config != None:
                        ## None means config was "commented out" with "_config_name"
                        setattr(obj, field_name, nested_config)
            self._handle_lists(field_type, field_name, obj)

    def _load_clazz(self, _config_name):
        ## load the *Config module and get the clazz
        config_name = snake_to_pascal(_config_name)
        module = importlib.import_module(f"configs.{_config_name}_config")
        clazz_name = f"{config_name}Config"
        _print(f"Loading '{config_name}' config, class {clazz_name} from {module.__name__}")
        clazz = getattr(module, clazz_name, None)
        return clazz

    def _load_config(self, config_name, values: dict):
        if config_name.startswith("_"):
            ## fields beginning with underscores are skipped (commented out)
            return None
        if type(values) != dict:
            ## make sure we're working on a dictonary
            raise Exception(f"'{config_name}' expects a dictionary, but got '{values}' ({type(values)})")
        clazz = self._load_clazz(config_name)
        _trace(clazz, values)
        obj = self._handle_fields(clazz, values)
        self._handle_strict_types(clazz, obj)
        self._handle_dicts(clazz, obj)
        return obj

    def _rename_class_to_clazz(self, obj):
        ## recursively descend into the object converting "class" into "clazz"
        if isinstance(obj, dict):
            keys = list(obj.keys())
            for key in keys:
                if key == "class":
                    obj["clazz"] = obj.pop("class")
                else:
                    self._rename_class_to_clazz(obj[key])

    def from_file(self, fname: str, with_config:str=None) -> "PMConfig":
        try:
            obj = json_read(fname)
            self._rename_class_to_clazz(obj)
            _print("with_config", with_config)
            return self.from_dict(obj, with_config=with_config)
        except Exception as e:
            raise TypeError(f"error reading file '{fname}. {str(e)}")

    def from_string(self, data: str, with_config:str=None) -> "PMConfig":
        obj = json_loads(data)
        if not obj:
            raise Exception(f"bad json object: '{data[0:20]}...'")
        return self.from_dict(obj, with_config=with_config)

    def from_dict(self, obj: dict, with_config:str = None) -> "PMConfig":
        result = None
        if with_config:
            result = self._load_config(with_config, obj)
        else:
            result = self._load_config("config", obj)
        return result
    
    
if __name__ == "__main__":
    pmconfig = PMConfig()
    def test_01_simple():
        foo = "{}"
        obj = pmconfig.from_string(foo)
        d = to_dict(obj)
        _print("test_01_simple", json_dumps(d))
        if d != {}:
            raise Exception("test_01_simple failed")

    def test_02_pmmodule_1():
        test = \
"""{
  module: {
    name: null,
    position: "None",
    subscriptions: null,
    disabled: false,
    force_render: false,
    force_update: false,
    color: "#fff",
    bg_color: null,
    text_color: "#fff",
    text_bg_color: null,
    font_name: "DejaVuSans",
    font_size: 64,
    font_baseline: false,
    font_y_offset: 0,
  },
}"""
        foo = "{module: {}}"
        obj = pmconfig.from_string(foo, "moddef")
        result = json_dumps(obj)
        _print(f"'\n{test}\n'")
        _print(f"'\n{result}\n'")
        if result != test:
            raise Exception("test_02_pmconfig_1 failed")

    def test_02_pmmodule_2():
        test = \
"""{
  module: {
    name: "weather",
    position: "None",
    subscriptions: null,
    disabled: false,
    force_render: false,
    force_update: false,
    color: "#999",
    bg_color: null,
    text_color: "#fff",
    text_bg_color: null,
    font_name: "DejaVuSans",
    font_size: 64,
    font_baseline: false,
    font_y_offset: 0,
  },
}"""
        foo = "{module: {name: 'weather', color: '#999'}}"
        obj = pmconfig.from_string(foo, "moddef")
        result = json_dumps(obj)
        _print(f"'\n{test}\n'")
        _print(f"'\n{result}\n'")
        if result != test:
            raise Exception("test_02_pmmodule_2 failed")

    def test_02_pmmodule_3():
        test = \
"""{
  module: {
    name: "weather",
    position: "None",
    subscriptions: null,
    disabled: false,
    force_render: false,
    force_update: false,
    color: "#999",
    bg_color: null,
    text_color: "#fff",
    text_bg_color: null,
    font_name: "DejaVuSans",
    font_size: 64,
    font_baseline: false,
    font_y_offset: 0,
    other: "Other",
  },
}"""
        foo = "{module: {name: 'weather', color: '#999', 'other': 'Other'}}"
        obj = pmconfig.from_string(foo, "moddef")
        result = json_dumps(obj)
        _print(f"'\n{test}\n'")
        _print(f"'\n{result}\n'")
        if result != test:
            raise Exception("test_02_pmmodule_3 failed")

    def test_03_config_1():
        obj = pmconfig.from_file("./src/configs/test_data/config.json", with_config="pymirror")
        result = json_dumps(obj)
        _print(f"'\n{result}\n'")

    def arg_parser():
        import argparse
        parser = argparse.ArgumentParser(description="Test PMConfig")
        parser.add_argument("--file", "-f", type=str, help="Input file")
        return parser.parse_args()

    def main():
        args = arg_parser()
        _print(args)
        # test_01_simple()
        # test_02_pmmodule_1()
        # test_02_pmmodule_2()
        # test_02_pmmodule_3()
        # test_03_config_1()
        if args.file:
            obj = pmconfig.from_file(args.file)
            result = json_dumps(obj)
            _print(f"'\n{result}\n'")

    main()
