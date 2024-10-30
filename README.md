# pydrantic

## What is This?

pydrantic is a Python configuration library. The project is heavily inspired by [Hydra](https://hydra.cc/), which provides helpful command-line overrides and allows for a lot of flexiblity. While Hydra uses YAML as a config definition language (which can be unwieldly to work with), pydrantic uses Python. The goal of the project is to let you write your configs in the same language that your code is in, while trying to keep the same level of flexibility and ease-of-use.

## Installation

To install the latest release from PyPI:
```bash
git clone https://github.com/seyuboglu/pydrantic.git
cd pydrantic
pip install -e .
```


# Usage

## The Basics

`pydrantic` is a fork of Jordan's awesome `pydra` library. 
`pydrantic` inherits the same CLI syntax from `pydra`, but uses [Pydantic](https://docs.pydantic.dev/latest/) models for config classes.
So, in some sense, `pydrantic` is just a more opinionated version of `pydra`. 

The choice of Pydantic models for config classes encourages a strict separation between config and functionality. It also enables a few nice features like safer serialization, built-in type validation, and dependencies between fields in the config.

```python
import pydrantic

class MyConfig(pydrantic.RunConfig):

    foo: int = 5
    bar: int = 10

    def run(self):
        print(f"foo: {self.foo}")
        print(f"bar: {self.bar}")

if __name__ == "__main__":
    config = MyConfig()
    pydrantic.main(config)
```



You can run this script with:

```bash
python script.py

python script.py -u foo=10
```


## Nested Configs

Configs can contain nested Pydantic models or dictionaries.

```python
from pydrantic import RunConfig
from pydantic import BaseModel

class InnerConfig(BaseModel):
    x: int = 1
    y: int = 2

class MyConfig(RunConfig):
    inner: InnerConfig = InnerConfig()

    def run(self):
        print(f"Inner x: {self.inner.x}")
        print(f"Inner y: {self.inner.y}")

if __name__ == "__main__":
    config = MyConfig()
    main(config)
```

You can access nested fields from the command line using dots:

```bash
python script.py -u inner.x=5
```

## `--in`

You can also temporarily scope your assignments to a nested config using the `--in` flag. Use `in--` to end the scoping region. Using the above example:

```bash
python script.py --in inner x=5 y=10 in-- --in d a=100 b=101 in--
```

## Required Variables

pydrantic supports marking certain configuration variables as required. If a required variable is not set, pydrantic will raise an error.

```python
import pydrantic

class MyConfig(pydrantic.Config):
    def __init__(self):
        super().__init__()
        self.optional = 5
        self.required = pydrantic.REQUIRED

@pydrantic.main(MyConfig)
def main(config: MyConfig):
    print(f"Optional: {config.optional}")
    print(f"Required: {config.required}")

if __name__ == "__main__":
    main()
```

Running this script without setting the required variable will result in an error:

```bash
python script.py  # Error: Required variable 'required' not set
python script.py required=10  # This will work
```

## `--list`

Often it can be handy to make a list using space delimiters. pydrantic supports this with the `--list` flag.

```python
import pydrantic

class MyConfig(pydrantic.Config):
    def __init__(self):
        super().__init__()
        self.x = None
        self.y = 1

@pydrantic.main(MyConfig)
def main(config: MyConfig):
    print(f"x: {config.x}")
    print(f"y: {config.y}")

if __name__ == "__main__":
    main()
```


```bash
python script.py --list x 1 2 3 list-- y=4

# This is equivalent to
python script.py 'x=[1,2,3]' y=4
```

## `--show`

Pass the `--show` flag at any point on the command line to print out the configuration (after applying all overrides and calling `finalize`) and then end the program. Using the above example:

```bash
python script.py --list x 1 2 3 list-- y=4 --show
```

## Aliases

Aliases in pydrantic allow you to create alternative names for configuration variables. This can be useful for creating shortcuts or more intuitive command-line interfaces.

```python
import pydrantic

class MyConfig(pydrantic.Config):
    def __init__(self):
        super().__init__()
        self.very_long_variable_name = 42
        self.short = pydrantic.Alias("very_long_variable_name")

@pydrantic.main(MyConfig)
def main(config: MyConfig):
    print(f"Value: {config.very_long_variable_name}")

if __name__ == "__main__":
    main()
```

You can now use either the original name or the alias on the command line:

```bash
python script.py very_long_variable_name=100
# or
python script.py short=100
```

Both will set the same variable.

## Working with Data Classes

pydrantic also supports incorporating data classes into configs. Use `pydrantic.DataclassWrapper` to create an object that you can assign into from the CLI. Call `build()` on the object to get the dataclass instance.

```python
import pydrantic
from dataclasses import dataclass

@dataclass
class InnerConfig:
    x: int
    y: int
    z: int = 11

class MyConfig(pydrantic.Config):
    def __init__(self):
        super().__init__()
        self.dc = pydrantic.DataclassWrapper(InnerConfig)


@pydrantic.main(MyConfig)
def main(config: MyConfig):
    dc = config.dc.build()
    print("dc", dc)

if __name__ == "__main__":
    main()
```

pydrantic will prevent you from setting dataclass fields that don't exist, and make sure that all required fields are set.

```bash
python script.py dc.x=5 dc.y=10 # good
python script.py dc.z=20 dc.y=10 dc.x=5 # also good
python script.py dc.x=5 # error, missing required field y
python script.py dc.x=5 dc.w=30 # error, w is not a field
```

## Serializing Configs

To produce a human-readable serialization of your config, you can use the `to_dict()` method. We also provide a few helper functions to save configs to YAML, pickle, or dill files.

```python
import pydrantic

class MyConfig(pydrantic.Config):
    def __init__(self):
        super().__init__()
        self.x = 5
        self.y = 10

@pydrantic.main(MyConfig)
def main(config: MyConfig):
    as_dict = config.to_dict()
    print(as_dict)

    pydrantic.save_yaml(as_dict, "conf.yaml")
    pydrantic.save_pickle(as_dict, "conf.pkl")
    pydrantic.save_dill(as_dict, "conf.dill")

if __name__ == "__main__":
    main()
```

## pydrantic without `main`

You can also apply pydrantic overrides programmatically with `apply_overrides`, which takes in a `Config` instance and a list of args.

```python
import pydrantic

class MyConfig(pydrantic.Config):
    def __init__(self):
        super().__init__()
        self.x = 5
        self.y = 10


config = MyConfig()
pydrantic.apply_overrides(config, ["x=20", "y=30"])

print(config.to_dict())
```

# Running Tests

To run the repo's test suite, use:

```bash
python -m unittest discover tests
```