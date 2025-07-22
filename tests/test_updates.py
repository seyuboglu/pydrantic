import pytest
from pydrantic.config import BaseConfig, RunConfig
from pydrantic.cli import _update_config
from pydantic import Field

from pydrantic.variables import FormatStringVariable

class NestedConfig(BaseConfig):
    nested_param1: float = Field(default=0.1)
    nested_param2: str = Field(default="nested_default")

class SimpleConfig(RunConfig):
    param1: int = Field(default=1)
    param2: str = Field(default="default")
    param3: str = Field(default="default")
    nested: NestedConfig = Field(default_factory=NestedConfig)
    
    def run(self):
        pass

def test_override_top_level_fields():
    config = SimpleConfig()
    updates = ["param1=10", "param2=updated_value"]
    updated_config = _update_config(config, updates)
    assert updated_config.param1 == 10
    assert updated_config.param2 == "updated_value"

def test_override_nested_fields():
    config = SimpleConfig()
    updates = ["nested.nested_param1=3.14", "nested.nested_param2=pi"]
    updated_config = _update_config(config, updates)
    assert updated_config.nested.nested_param1 == 3.14
    assert updated_config.nested.nested_param2 == "pi"

def test_override_mixed_fields():
    config = SimpleConfig()
    updates = ["param1=42", "nested.nested_param1=2.718"]
    updated_config = _update_config(config, updates)
    assert updated_config.param1 == 42
    assert updated_config.nested.nested_param1 == 2.718

def test_invalid_override_raises_attribute_error():
    config = SimpleConfig()
    updates = ["invalid_param=123"]
    with pytest.raises(AttributeError):
        _update_config(config, updates)

def test_type_conversion():
    config = SimpleConfig()
    updates = ["param1=20", "nested.nested_param1=100"]
    updated_config = _update_config(config, updates)
    assert isinstance(updated_config.param1, int)
    assert updated_config.param1 == 20
    assert isinstance(updated_config.nested.nested_param1, float)
    assert updated_config.nested.nested_param1 == 100.0

class DeepNestedConfig(BaseConfig):
    level3_param: str = Field(default="level3_default")

class Level2Config(BaseConfig):
    level2_param: int = Field(default=2)
    level3: DeepNestedConfig = Field(default_factory=DeepNestedConfig)

class ComplexConfig(BaseConfig):
    level1_param: str = Field(default="level1_default")
    level2: Level2Config = Field(default_factory=Level2Config)


def test_override_deeply_nested_fields():
    config = ComplexConfig()
    updates = [
        "level1_param=updated_level1",
        "level2.level2_param=99",
        "level2.level3.level3_param=deep_value"
    ]
    updated_config = _update_config(config, updates)
    assert updated_config.level1_param == "updated_level1"
    assert updated_config.level2.level2_param == 99
    assert updated_config.level2.level3.level3_param == "deep_value"


def test_override_deeply_nested_fields():
    config = ComplexConfig()
    updates = [
        "level1_param=updated_level1",
        "level2.level2_param=99",
        "level2.level3.level3_param=deep_value"
    ]
    updated_config = _update_config(config, updates)
    assert updated_config.level1_param == "updated_level1"
    assert updated_config.level2.level2_param == 99
    assert updated_config.level2.level3.level3_param == "deep_value"

def test_override_variables():
    from pydrantic.variables import FormatStringVariable
    config = SimpleConfig(
        param1=1,
        param2=FormatStringVariable("Hello, {param1}!")
    )
    updates = ["param1=10"]
    updated_config = _update_config(config, updates)
    assert updated_config.param1 == 10
    assert updated_config.param2 == "Hello, 10!"

def test_override_variables_with_nested_config_and_flat_keys():
    config = SimpleConfig(
        param1=1,
        nested=NestedConfig(
            nested_param1=0.1, 
            nested_param2=FormatStringVariable("Hello, {nested_param1}!")
        )
    )
    
    updates = ["nested.nested_param1=10.0"]
    updated_config = _update_config(config, updates)
    
    assert updated_config.nested.nested_param1 == 10.0
    assert updated_config.nested.nested_param2 == "Hello, 10.0!"

def test_override_variable_with_nested_config_and_nested_keys():
    config = SimpleConfig(
        param1=1,
        param2=FormatStringVariable("Hello, {nested.nested_param1}!"),
        nested=NestedConfig(
            nested_param1=0.1, 
            nested_param2=FormatStringVariable("Hello, {nested_param1}!")
        )
    )
    updates = ["nested.nested_param1=10.0"]
    updated_config = _update_config(config, updates)
    assert updated_config.nested.nested_param1 == 10.0
    assert updated_config.nested.nested_param2 == "Hello, 10.0!"
    assert updated_config.param2 == "Hello, 10.0!"


def test_override_variable_with_nested_config_and_nested_keys():
    config = SimpleConfig(
        param1=1,
        param2=FormatStringVariable("Hello, {param3}!"),
        param3=FormatStringVariable("Hello, {nested.nested_param2}!"),
        nested=NestedConfig(
            nested_param1=0.1, 
            nested_param2=FormatStringVariable("Hello, {nested_param1}!")
        )
    )
    updates = ["nested.nested_param1=10.0"]
    updated_config = _update_config(config, updates)
    assert updated_config.nested.nested_param1 == 10.0
    assert updated_config.nested.nested_param2 == "Hello, 10.0!"
    assert updated_config.param3 == "Hello, Hello, 10.0!!"
    assert updated_config.param2 == "Hello, Hello, Hello, 10.0!!!"