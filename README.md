# pydrantic

## What is This?
`pydrantic` is a simple library that makes it easier to use Pydantic models as configs for machine learning experiments. 
The library augments Pydantic models with features inspired by other configuration libraries like (*e.g.* [Hydra](https://hydra.cc/)). These include:

- **Command-line overrides**: Users can override config fields from the command line.
- **Serialization**: Users can serialize configs to YAML, pickle, or dill files.
- **Variables**: Users can define variables that can be used in the config.
- **Launching sweeps**: Users can launch sweeps from the command line.
- **Object instantiation**: Users can instantiate Pydantic models from the command line or from a file.

*Why use Pydantic models as configs?*
`pydrantic` is a fork of Jordan's awesome `pydra` library. 
`pydrantic` inherits the same CLI syntax from `pydra`, but uses [Pydantic](https://docs.pydantic.dev/latest/) models for config classes.
So, in some sense, `pydrantic` is just a more opinionated version of `pydra`. 

The choice of Pydantic models for config classes encourages a strict separation between config and functionality. It also enables a few nice features like safer serialization, built-in type validation, and dependencies between fields in the config.


## Installation

To install the latest release from PyPI:
```bash
pip install pydrantic
```

To install from source:
```bash
git clone https://github.com/seyuboglu/pydrantic.git
cd pydrantic
pip install -e .
```


# Usage

## The Basics
Define the schema for your config in a file called `config.py`.

In this example, we will define a `TrainConfig` class that specifies the schema of a configuration for a training run.
Note that we inherit from `RunConfig`, which is a convenience class that adds a few useful features to the base `BaseConfig` class.

```python
# path/to/config.py
from pydrantic import RunConfig

class TrainConfig(RunConfig):
    
    # (1) define the fields for your config
    lr: float = 1e-3
    epochs: int = 10
    batch_size: int = 128

    # (2) define a method that will be called when the config is run
    def run(self):
        ...
```

Now in separate file, you can define a script that instantiates a config and runs it:
1. Instantiate the config with the desired values.
2. Launch the config with `pydrantic.main`. By using `pydrantic.main`, you can override the values of the config fields from the command line.

```python
# path/to/script.py
from config import TrainConfig

# (1) instantiate the config
config = TrainConfig(
    lr=1e-4,
    epochs=20,
    batch_size=256,
)

if __name__ == "__main__":
    # (3) run the config
    pydrantic.main(config)
```

You can run this script with:

```bash
python path/to/script.py
```

Or override the values of specific fields:
```bash
python path/to/script.py lr=1e-5
```


## Nesting Configs

Just like Pydantic models, configs can be nested.

```python
# path/to/config.py
from pydrantic import BaseConfig, RunConfig

class ModelConfig(BaseConfig):
    num_layers: int = 1
    hidden_dim: int = 1024

class TrainConfig(RunConfig):
    model: ModelConfig

    lr: float = 1e-3
    epochs: int = 10
    batch_size: int = 128

    def run(self):
        ...
```
Now, in a separate script, you can instantiate the config and run it:

```python
# path/to/script.py
from config import TrainConfig, ModelConfig

# (1) instantiate the config
config = TrainConfig(
    model=ModelConfig(
        num_layers=10,
        hidden_dim=1024,
    ),
    lr=1e-4,
    epochs=20,
    batch_size=256,
)

if __name__ == "__main__":
    # (3) run the config
    pydrantic.main(config)
```

You can set nested fields from the command line using dots:

```bash
python script.py model.num_layers=5
```

## Launching Sweeps
You can sweep over different configurations by creating a list of configs in a script. 
For example, assuming you have defined a `TrainConfig` class in another file, you can 
run a sweep over learning rates by creating a file `path/to/script.py` with the following contents:

```python
# path/to/script.py
from ... import TrainConfig
import numpy as np

configs = []
for lr in np.logspace(-4, -2, 10):
   configs.append(
    TrainConfig(learning_rate=lr)
   ) 

if __name__ == "__main__":
    pydrantic.main(configs)
```

To launch the runs in parallel using Ray, you can run the script with the `-p` flag:
```bash
python path/to/script.py -p
```


## Object Configs

We also provide support for creating configs that 



We also provide a few helper functions to save configs to YAML, pickle, or dill files.
For example:

```python
config = MyConfig()

config.to_yaml("conf.yaml")
config = MyConfig.from_yaml("conf.yaml")


if __name__ == "__main__":
    main()
```
# Dev

## Running Tests

To run the repo's test suite, use:

```bash
python -m unittest discover tests
```

## Releasing 
First bump the version in `setup.py` and commit the changes.
```
python3 -m pip install --upgrade build
python3 -m build
python3 -m pip install --upgrade twine
python3 -m twine upload --repository pypi dist/*   
```
