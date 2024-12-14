import pytest
from pathlib import Path
import yaml
import os
from typing import Type

from pydrantic import BaseConfig

class SimpleConfig(BaseConfig):
    x: int = 1
    y: str = "hello"
    t: Type = BaseConfig 

class NestedConfig(BaseConfig):
    x: int = 1
    y: str = "hello"
    simple: SimpleConfig

class OuterClass:
    class InnerConfig(BaseConfig):
        x: int = 1
        y: str = "hello"

@pytest.fixture
def tmp_dir(tmp_path):
    """Fixture to provide a temporary directory."""
    return tmp_path

def test_to_from_yaml(tmp_dir):
    # Create config
    config = SimpleConfig(x=42, y="world")
    
    # Save to yaml
    yaml_path = tmp_dir / "config.yaml"
    config.to_yaml(str(yaml_path))
    
    # Verify file exists
    assert yaml_path.exists()
    
    # Load from yaml
    loaded_config = SimpleConfig.from_yaml(str(yaml_path))
    
    # Verify contents
    assert loaded_config.x == 42
    assert loaded_config.y == "world"
    assert loaded_config.t == BaseConfig

def test_to_from_dill(tmp_dir):
    config = SimpleConfig(x=42, y="world")
    
    dill_path = tmp_dir / "config.dill"
    config.to_dill(str(dill_path))
    
    assert dill_path.exists()
    
    loaded_config = SimpleConfig.from_dill(str(dill_path))
    assert loaded_config.x == 42
    assert loaded_config.y == "world"

def test_to_from_pickle(tmp_dir):
    config = SimpleConfig(x=42, y="world")
    
    pickle_path = tmp_dir / "config.pkl"
    config.to_pickle(str(pickle_path))
    
    assert pickle_path.exists()
    
    loaded_config = SimpleConfig.from_pickle(str(pickle_path))
    assert loaded_config.x == 42
    assert loaded_config.y == "world"

def test_nested_config_serialization(tmp_dir):
    inner = SimpleConfig(x=42, y="world")
    nested = NestedConfig(x=100, y="outer", simple=inner)
    
    # Test YAML
    yaml_path = tmp_dir / "nested.yaml"
    nested.to_yaml(str(yaml_path))
    
    loaded_nested = NestedConfig.from_yaml(str(yaml_path))
    assert loaded_nested.x == 100
    assert loaded_nested.y == "outer"
    assert loaded_nested.simple.x == 42
    assert loaded_nested.simple.y == "world"

def test_inner_class_config_serialization(tmp_dir):
    inner_config = OuterClass.InnerConfig(x=42, y="world")
    
    yaml_path = tmp_dir / "inner.yaml"
    inner_config.to_yaml(str(yaml_path))
    
    loaded_config = OuterClass.InnerConfig.from_yaml(str(yaml_path))
    assert loaded_config.x == 42
    assert loaded_config.y == "world"

def test_strict_loading():
    # Create a dict with extra fields
    invalid_data = {
        "_config_type": {
            "_is_type": True,
            "_module": "test_io",
            "_qualname": "SimpleConfig"
        },
        "x": 42,
        "y": "world",
        "z": "extra"  # Extra field
    }
    
    # Should raise error in strict mode
    with pytest.raises(ValueError):
        SimpleConfig.from_dict(invalid_data, strict=True)
    
    # Should work in non-strict mode
    config = SimpleConfig.from_dict(invalid_data, strict=False)
    assert config.x == 42
    assert config.y == "world"
    assert not hasattr(config, "z")

def test_type_serialization(tmp_dir):
    config = SimpleConfig(x=42, y="world", t=NestedConfig)
    
    yaml_path = tmp_dir / "type.yaml"
    config.to_yaml(str(yaml_path))
    
    loaded_config = SimpleConfig.from_yaml(str(yaml_path))
    assert loaded_config.t == NestedConfig