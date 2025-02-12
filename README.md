# pydrantic

## What is This?
`pydrantic` is a simple library that makes it easier to use Pydantic models as configs for machine learning experiments. 
The library provides utilities that Pydantic models with features inspired by other configuration libraries like (*e.g.* [Hydra](https://hydra.cc/)). These include:

- **Command-line overrides**: Users can override config fields from the command line.
- **Serialization**: Users can serialize configs to YAML, pickle, or dill files.
- **Variables**: Users can define variables that can be used in the config.
- **Launching sweeps**: Users can launch sweeps from the command line.
- **Object instantiation**: Users can instantiate Pydantic models from the command line or from a file.

*Why use Pydantic models as configs?*


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


Both will set the same variable.


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

# Running Tests

To run the repo's test suite, use:

```bash
python -m unittest discover tests
```