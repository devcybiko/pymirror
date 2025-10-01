

from dataclasses import fields
import importlib
from typing import get_type_hints
from pymirror.utils.utils import json_dumps, json_loads, json_read, snake_to_pascal, to_dict
from pymirror.pmlogger import trace, trace_method, _trace, _debug

class Object:
    def __init__(self):
        pass

@trace
class PMModel:
    """
    NOTE: Also used as a "marker" for instantiated Models

    Pulls in "models" from json or dicts.
    Models are dataclasses which gives us strong type checking
    The models are defined in the current package
    And they are expected to include default values.
    """
    def __init__(self):
        pass

    def _strict_types(self, clazz, obj):
        """Validate and convert types after initialization"""
        type_hints = get_type_hints(clazz)
        for field_name, expected_type in type_hints.items():
            if hasattr(obj, field_name):
                value = getattr(obj, field_name)
                expected_type = getattr(expected_type, '__origin__', expected_type)
                _debug("###", field_name, expected_type)
                if value is not None:
                    if isinstance(value, dict):
                        setattr(obj, field_name, value)
                    elif not isinstance(value, expected_type):
                        try:
                            # Try to convert the type
                            converted_value = expected_type(value)
                            setattr(obj, field_name, converted_value)
                        except (ValueError, TypeError) as e:
                            raise TypeError(f"Field '{clazz.__name__}.{field_name}' expected {expected_type.__name__}, got {type(value).__name__}: {value}")
    @trace_method
    def _specific_fields(self, clazz, values):
        field_names = {f.name for f in fields(clazz)}
        valid_values = {k: v for k, v in values.items() if k in field_names}
        obj = clazz(**valid_values)
        # Add invalid fields as attributes
        for k, v in values.items():
            if k not in field_names:
                setattr(obj, k, v)
        return obj

    def _load_model(self, _model_name, values: dict, /, strict_names: bool = True, strict_types: bool = True):
        if _model_name.startswith("_"):
            ## commented-out model
            return None
        model_name = snake_to_pascal(_model_name)
        module = importlib.import_module(f"models.{_model_name}_model")
        clazz_name = f"{model_name}Model"
        _debug(f"Loading '{_model_name}' model, class {clazz_name} from {module.__name__}")
        clazz = getattr(module, clazz_name, None)
        if type(values) != dict:
            raise Exception(f"'{_model_name}' expects a dictionary, but got '{values}' ({type(values)})")
        if strict_names:
            ## allow only the members in the dataclass
            ## extra / unknown members will throw an exception
            obj = clazz(**values)
        else:
            ## get all the default values
            ## then overlay with new values and additional fields
            _debug("... trying not strict_names")
            _trace(clazz, values)
            obj = self._specific_fields(clazz, values)

        if strict_types:
            self._strict_types(clazz, obj)
        ## iterate over all the values. any dicts will be imported as models
        type_hints = get_type_hints(clazz)
        for field in fields(obj):
            field_name = field.name
            field_value = getattr(obj, field_name)
            field_type = type_hints.get(field_name)
            _debug(field_name, field_type)
            _debug(">>>", field_name, field_type.__name__, field_value)
            # Check if field value is a dict that should be converted to a model
            if isinstance(field_value, dict) and field_type != dict:
                # Convert dict to model recursively
                if field_type.__name__.endswith("Model"):
                    ## crude way to determine, but...
                    nested_model = self._load_model(field_type.__name__.lower().replace('model', ''), field_value, strict_names=strict_names, strict_types=strict_types)
                    if nested_model != None:
                        ## None means model was "commented out" with "_model_name"
                        setattr(obj, field_name, nested_model)
                else:
                    nested_model = self._load_model(field_name, field_value, strict_names=strict_names, strict_types=strict_types)
                    if nested_model != None:
                        ## None means model was "commented out" with "_model_name"
                        setattr(obj, field_name, nested_model)
        # For non-dataclass objects, just iterate __dict__
        for attr_name, attr_value in obj.__dict__.items():
            if attr_name in type_hints:
                continue
            _debug("<<<", attr_name, attr_value, "(non-dataclass)")
            if isinstance(attr_value, dict):
                nested_model = self._load_model(attr_name, attr_value, strict_names=strict_names, strict_types=strict_types)
                if nested_model != None:
                    ## None means model was "commented out" with "_model_name"
                    setattr(obj, attr_name, nested_model)
        return obj

    def _translate_class_to_clazz(self, obj):
        ## recursively descend into the object converting keys "class" into "clazz"
        if isinstance(obj, dict):
            keys = list(obj.keys())
            for key in keys:
                if key == "class":
                    obj["clazz"] = obj.pop("class")
                else:
                    self._translate_class_to_clazz(obj[key])

    def from_file(self, fname: str, keys: list[str] = None, /, with_model:str=None, strict_names: bool = True, strict_types = True) -> "PMModel":
        """ 
        Pulls all the models from the dict that are defined
        in the models module.
        if a model is in "keys[]" but is not in the json
        then it is imported, added, and the model's defaults are taken
        """
        try:
            obj = json_read(fname)
            self._translate_class_to_clazz(obj)
            print("with_model", with_model)
            return self.from_dict(obj, keys, with_model=with_model, strict_names=strict_names, strict_types=strict_types)
        except Exception as e:
            raise TypeError(f"error reading file '{fname}. {str(e)}")

    def from_string(self, data: str, keys: list[str] = None, /, with_model:str=None, strict_names: bool = True, strict_types = True) -> "PMModel":
        obj = json_loads(data)
        if not obj:
            raise Exception(f"bad json object: '{data[0:20]}...'")
        return self.from_dict(obj, keys, with_model=with_model, strict_names=strict_names, strict_types=strict_types)

    def from_dict(self, obj: dict, keys: list[str] = None, /, with_model:str = None, strict_names: bool = True, strict_types = True) -> "PMModel":
        result = Object()
        if with_model:
            obj = self._load_model(with_model, obj, strict_names=strict_names, strict_types=strict_types)
            if obj != None:
                ## None means model was "commented out" with "_model_name"
                setattr(result, with_model, obj)
        else:
            for key, value in obj.items():
                print("trying", key, value)
                obj = self._load_model(key, value, strict_names=strict_names, strict_types=strict_types)
                print("...", obj)
                if obj != None:
                    _debug("...", obj)
                    setattr(result, key, obj)
        return result
    
    
if __name__ == "__main__":
    pmmodel = PMModel()
    def test_01_simple():
        foo = "{}"
        obj = pmmodel.from_string(foo)
        d = to_dict(obj)
        print("test_01_simple", json_dumps(d))
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
        obj = pmmodel.from_string(foo, "moddef")
        result = json_dumps(obj)
        print(f"'\n{test}\n'")
        print(f"'\n{result}\n'")
        if result != test:
            raise Exception("test_02_pmmodel_1 failed")

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
        obj = pmmodel.from_string(foo, "moddef")
        result = json_dumps(obj)
        print(f"'\n{test}\n'")
        print(f"'\n{result}\n'")
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
        obj = pmmodel.from_string(foo, "moddef", strict_names=False)
        result = json_dumps(obj)
        print(f"'\n{test}\n'")
        print(f"'\n{result}\n'")
        if result != test:
            raise Exception("test_02_pmmodule_3 failed")

    def test_03_config_1():
        obj = pmmodel.from_file("./src/models/test_data/config.json", with_model="pymirror", strict_names=False)
        result = json_dumps(obj)
        print(f"'\n{result}\n'")

    def arg_parser():
        import argparse
        parser = argparse.ArgumentParser(description="Test PMModel")
        parser.add_argument("--file", "-f", type=str, help="Input file")
        return parser.parse_args()

    def main():
        args = arg_parser()
        print(args)
        # test_01_simple()
        # test_02_pmmodule_1()
        # test_02_pmmodule_2()
        # test_02_pmmodule_3()
        # test_03_config_1()
        if args.file:
            obj = pmmodel.from_file(args.file, strict_names=False)
            result = json_dumps(obj)
            print(f"'\n{result}\n'")

    main()
