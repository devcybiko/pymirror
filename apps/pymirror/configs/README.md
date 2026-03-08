# CONFIGS

- In PyMirror I've tried to emulate the Java concept of "everything's a class."
- But maintain the interpretive nature of Python
- So, every config element in the config.json must have a class to define it.
- This enforces correct spelling of fields within the configs
- Likewise, you can't have a config object without a config class
- So, ConfigConfig is a class containing all the configs that can be installed in the config.json
- When PyMirror loads, each module gets a configuration object that is attached to the ConfigConfig

## Adding a new configuration

- Adding a new module requires that you add a new Config class
- The file naming convention is <module>config.py
- The class naming convention is <Module>Config
- The config class is an @dataclass
- Each field should be specified with a type specifier and optional default value
    - `field: str = None`
- Any filed that is not given a default is assumed to be `required`
- @dataclasses help enforce this rigor

## Mixins

- There are some fields (attributes) that seem to recur quite a bit
- Like Font styles, Text styles, and Graphics elements
- These reusable sets of fields are stored in the `mixins` folder
- Using Python's multiple inheritance model, you can subclass the new Module with these other mixins

## Loading Config Files

- When a config file is loaded, 
- PyMirror assumes each key in the dict is the name of a Module.
- So, the dict is then read and mapped to the `<Module>Config` class
- Any extraneous fields are considered erroneous
- Any missing fields are given the default value specified in `<Module>Config`
- And if a fieild is missing and has no default, an exception is thrown

