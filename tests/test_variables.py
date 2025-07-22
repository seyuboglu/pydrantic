from pydantic import ValidationError
import pytest
from pydrantic.variables import FormatStringVariable, VariableResolutionError

def test_format_string_variable_simple():
    variable = FormatStringVariable("Hello, {name}!")
    data = {"name": "Alice"}
    result = variable.resolve(data)
    assert result == "Hello, Alice!"

def test_format_string_variable_nested():
    variable = FormatStringVariable("Hello, {user.name}! You have {user.notifications} notifications.")
    data = {
        "user": {
            "name": "Bob",
            "notifications": 5
        }
    }
    result = variable.resolve(data)
    assert result == "Hello, Bob! You have 5 notifications."

def test_format_string_variable_deeply_nested():
    variable = FormatStringVariable("Coordinates: ({location.latitude}, {location.longitude})")
    data = {
        "location": {
            "latitude": 51.5074,
            "longitude": -0.1278
        }
    }
    result = variable.resolve(data)
    assert result == "Coordinates: (51.5074, -0.1278)"

def test_format_string_variable_list_access():
    variable = FormatStringVariable("First item: {items.0}, Second item: {items.1}")
    data = {
        "items": ["apple", "banana", "cherry"]
    }
    result = variable.resolve(data)
    assert result == "First item: apple, Second item: banana"

def test_format_string_variable_missing_key():
    variable = FormatStringVariable("Hello, {name}!")
    data = {}
    with pytest.raises(KeyError):
        variable.resolve(data)

def test_format_string_variable_partial_data():
    variable = FormatStringVariable("{greeting}, {user.name}!")
    data = {
        "greeting": "Hi",
        "user": {}
    }
    with pytest.raises(KeyError):
        variable.resolve(data)

def test_format_string_variable_special_characters():
    variable = FormatStringVariable("Path: {config.path}")
    data = {
        "config": {
            "path": "/usr/local/bin"
        }
    }
    result = variable.resolve(data)
    assert result == "Path: /usr/local/bin"

def test_format_string_variable_numeric_keys():
    variable = FormatStringVariable("Value: {data.2021}")
    data = {
        "data": {
            "2021": 100
        }
    }
    result = variable.resolve(data)
    assert result == "Value: 100"

def test_format_string_variable_with_flattened_dict():
    variable = FormatStringVariable("Total: {order.total}, Items: {order.items.0}, {order.items.1}")
    data = {
        "order": {
            "total": 250,
            "items": ["book", "pen"]
        }
    }
    result = variable.resolve(data)
    assert result == "Total: 250, Items: book, pen"

# def test_format_string_variable_escape_braces():
#     variable = FormatStringVariable("Use double braces to escape: {{}}")
#     data = {}
#     result = variable.resolve(data)
#     assert result == "Use double braces to escape: {}"

def test_format_string_variable_complex_nested():
    variable = FormatStringVariable("{user.name} - {user.details.address.city}, {user.details.address.country}")
    data = {
        "user": {
            "name": "Charlie",
            "details": {
                "address": {
                    "city": "New York",
                    "country": "USA"
                }
            }
        }
    }
    result = variable.resolve(data)
    assert result == "Charlie - New York, USA"

def test_format_string_variable_with_numbers_in_keys():
    variable = FormatStringVariable("Version: {version.v1_0}")
    data = {
        "version": {
            "v1_0": "stable"
        }
    }
    result = variable.resolve(data)
    assert result == "Version: stable"

def test_format_string_variable_list_of_dicts():
    variable = FormatStringVariable("First user: {users.0.name}, Second user: {users.1.name}")
    data = {
        "users": [
            {"name": "Alice"},
            {"name": "Bob"}
        ]
    }
    result = variable.resolve(data)
    assert result == "First user: Alice, Second user: Bob"

def test_format_string_variable_nested_list():
    variable = FormatStringVariable("First item of first list: {data.lists.0.0}")
    data = {
        "data": {
            "lists": [
                ["a1", "a2"],
                ["b1", "b2"]
            ]
        }
    }
    result = variable.resolve(data)
    assert result == "First item of first list: a1"

def test_format_string_variable_non_string_values():
    variable = FormatStringVariable("Is active: {active}, Count: {count}")
    data = {
        "active": True,
        "count": 42
    }
    result = variable.resolve(data)
    assert result == "Is active: True, Count: 42"

# def test_format_string_variable_with_format_spec():
#     variable = FormatStringVariable("Percentage: {value:.2f}%")
#     data = {
#         "value": 99.12345
#     }
#     result = variable.resolve(data)
#     assert result == "Percentage: 99.12%"

def test_format_string_variable_flat_keys_conflict():
    variable = FormatStringVariable("Value: {a.b}")
    data = {
        "a": {
            "b": 1
        },
        "a.b": 2
    }
    result = variable.resolve(data)
    assert result == "Value: 2"  # 'a.b' key overwrites 'a' -> 'b'

def test_format_string_variable_empty_template():
    variable = FormatStringVariable("")
    data = {"any": "data"}
    result = variable.resolve(data)
    assert result == ""

def test_format_string_variable_none_values():
    variable = FormatStringVariable("Maybe: {value}")
    data = {
        "value": None
    }
    result = variable.resolve(data)
    assert result == "Maybe: None"


def test_format_string_variable_in_config():
    from pydrantic.config import BaseConfig
    class Config(BaseConfig):
        foo: int = 1
        bar: int = 2
        name: str = "Hello"

    config = Config(
        foo=3, 
        name=FormatStringVariable("Hello, {foo}!")
    )
    assert config.name == "Hello, 3!"


def test_cyclic_dependency():
    from pydrantic.config import BaseConfig
    class Config(BaseConfig):
        foo: str = "foo"
        bar: str = "bar"
        
    with pytest.raises(ValidationError, match="Max resolution"):
        config = Config(
            foo=FormatStringVariable("{bar}"),
            bar=FormatStringVariable("{foo}")
        )