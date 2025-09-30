

from dataclasses import fields
import importlib
from typing import get_type_hints
from pymirror.utils.utils import json_dumps, json_loads, json_read, snake_to_pascal, to_dict

class Object:
    def __init__(self):
        pass

def _strict_types(clazz, obj):
    """Validate and convert types after initialization"""
    type_hints = get_type_hints(clazz)
    for field_name, expected_type in type_hints.items():
        if hasattr(obj, field_name):
            value = getattr(obj, field_name)
            expected_type = getattr(expected_type, '__origin__', expected_type)
            print("###", field_name, expected_type)
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

def _specific_fields(clazz, values):
    field_names = {f.name for f in fields(clazz)}
    valid_values = {k: v for k, v in values.items() if k in field_names}
    obj = clazz(**valid_values)
    # Add invalid fields as attributes
    for k, v in values.items():
        if k not in field_names:
            setattr(obj, k, v)
    return obj

def _load_model(_model_name, values: dict, /, strict_names: bool = True, strict_types: bool = True):
    model_name = snake_to_pascal(_model_name)
    module = importlib.import_module(f"models.{_model_name}_model")
    clazz_name = f"{model_name}Model"
    print(f"Loading '{_model_name}' model, class {clazz_name} from {module.__name__}")
    clazz = getattr(module, clazz_name, None)
    print("clazz", values)
    if strict_names:
        ## allow only the members in the dataclass
        ## extra / unknown members will throw an exception
        obj = clazz(**values)
    else:
        ## get all the default values
        ## then overlay with new values and additional fields
        obj = _specific_fields(clazz, values)

    if strict_types:
        _strict_types(clazz, obj)
    ## iterate over all the values. any dicts will be imported as models
    type_hints = get_type_hints(clazz)
    for field in fields(obj):
        field_name = field.name
        field_value = getattr(obj, field_name)
        field_type = type_hints.get(field_name)
        print(field_name, field_type)
        print(">>>", field_name, field_type.__name__, field_value)
        # Check if field value is a dict that should be converted to a model
        if isinstance(field_value, dict) and field_type != dict:
            # Convert dict to model recursively
            if field_type.__name__.endswith("Model"):
                ## crude way to determine, but...
                nested_model = _load_model(field_type.__name__.lower().replace('model', ''), field_value, strict_names=strict_names, strict_types=strict_types)
                setattr(obj, field_name, nested_model)
            else:
                nested_model = _load_model(field_name, field_value, strict_names=strict_names, strict_types=strict_types)
                setattr(obj, field_name, nested_model)
    # For non-dataclass objects, just iterate __dict__
    for attr_name, attr_value in obj.__dict__.items():
        if attr_name in type_hints:
            continue
        print("<<<", attr_name, attr_value, "(non-dataclass)")
        if isinstance(attr_value, dict):
            nested_model = _load_model(attr_name, attr_value, strict_names=strict_names, strict_types=strict_types)
            setattr(obj, attr_name, nested_model)
    return obj


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

    @classmethod
    def from_file(cls, fname: str, keys: list[str] = None, /, with_model:str=None, strict_names: bool = True, strict_types = True) -> "PMModel":
        """ 
        Pulls all the models from the dict that are defined
        in the models module.
        if a model is in "keys[]" but is not in the json
        then it is imported, added, and the model's defaults are taken
        """
        try:
            obj = json_read(fname)
            return cls.from_dict(obj, keys, with_model=with_model, strict_names=strict_names, strict_types=strict_types)
        except Exception as e:
            raise TypeError(f"error reading file '{fname}. {str(e)}")

    @classmethod
    def from_string(cls, data: str, keys: list[str] = None, /, with_model:str=None, strict_names: bool = True, strict_types = True) -> "PMModel":
        obj = json_loads(data)
        if not obj:
            raise Exception(f"bad json object: '{data[0:20]}...'")
        return cls.from_dict(obj, keys, with_model=with_model, strict_names=strict_names, strict_types=strict_types)

    @classmethod
    def from_dict(cls, obj: dict, keys: list[str] = None, /, with_model:str = None, strict_names: bool = True, strict_types = True) -> "PMModel":
        result = Object()
        if with_model:
            obj = _load_model(with_model, obj, strict_names=strict_names, strict_types=strict_types)
            setattr(result, with_model, obj)
        else:
            for key, value in obj.items():
                print("trying", key, value)
                obj = _load_model(key, value, strict_names=strict_names, strict_types=strict_types)
                print("...", obj)
                setattr(result, key, obj)
        return result
    
    
if __name__ == "__main__":
    def test_01_simple():
        foo = "{}"
        obj = PMModel.from_string(foo)
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
        obj = PMModel.from_string(foo, "moddef")
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
        obj = PMModel.from_string(foo, "moddef")
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
        obj = PMModel.from_string(foo, "moddef", strict_names=False)
        result = json_dumps(obj)
        print(f"'\n{test}\n'")
        print(f"'\n{result}\n'")
        if result != test:
            raise Exception("test_02_pmmodule_3 failed")

    def test_03_config_1():
        obj = PMModel.from_file("./src/models/test_data/config.json", with_model="pymirror", strict_names=False)
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
            obj = PMModel.from_file(args.file, with_model="module", strict_names=False)
            result = json_dumps(obj)
            print(f"'\n{result}\n'")

    main()
