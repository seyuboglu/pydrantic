from pathlib import Path
import yaml
import dill
import pickle

from dataclasses import fields, MISSING

from copy import deepcopy


class _Required:
    pass


REQUIRED = _Required()

# https://stackoverflow.com/questions/6432605/any-yaml-libraries-in-python-that-support-dumping-of-long-strings-as-block-liter


class literal_unicode(str):
    pass


def literal_unicode_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


yaml.add_representer(literal_unicode, literal_unicode_representer)


def transform_into_literals(data):
    if isinstance(data, dict):
        data = {k: transform_into_literals(v) for k, v in data.items()}
        return data
    elif isinstance(data, list):
        return [transform_into_literals(x) for x in data]
    elif isinstance(data, str):
        if "\n" in data:
            return literal_unicode(data)
        else:
            return data
    else:
        return data


def load_yaml(path: Path):
    with open(path, "r") as f:
        data = yaml.load(f, Loader=yaml.CLoader)

    return data


def save_yaml(data, path: Path, sort_keys=True, transform=True):
    if transform:
        data = transform_into_literals(data)

    with open(path, "w") as f:
        yaml.dump(
            data,
            f,
            sort_keys=sort_keys,
        )


def load_dill(path: Path):
    with open(path, "rb") as f:
        data = dill.load(f)

    return data


def save_dill(data, path: Path):
    with open(path, "wb") as f:
        dill.dump(data, f)


def load_pickle(path: Path):
    with open(path, "rb") as f:
        data = pickle.load(f)

    return data


def save_pickle(data, path: Path):
    with open(path, "wb") as f:
        pickle.dump(data, f)


def load_binary(path: Path):
    if path.suffix == ".dill":
        return load_dill(path)
    elif path.suffix == ".pkl":
        return load_pickle(path)
    else:
        raise ValueError(f"Unknown extension {path.suffix}")


def import_object(name: str):
    """Import an object from a string.
    
    Parameters:
    - name (str): The name of the object to import.
    
    Returns:
    - object: The imported object.
    """
    import importlib
    module_name, obj_name = name.rsplit('.', 1)
    module = importlib.import_module(module_name.replace("olive", "haystacks"))
    return getattr(module, obj_name)



def unflatten_dict(d: dict, sep: str = "/") -> dict:
    """ 
    Takes a flat dictionary with '/' separated keys, and returns it as a nested dictionary.
    
    Parameters:
    d (dict): The flat dictionary to be unflattened.
    
    Returns:
    dict: The unflattened, nested dictionary.
    """
    result = {}

    for key, value in d.items():
        parts = key.split(sep)
        d = result
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value

    return result


def flatten_dict(d: dict, parent_key: str = '', sep: str = '/') -> dict:
    """
    Takes a nested dictionary and returns it as a flat dictionary with '/' separated keys.
    Supports lists by appending the index to the key path.
    
    Parameters:
    d (dict): The nested dictionary to be flattened.
    parent_key (str): The base key to use for the flattened keys.
    sep (str): The separator to use between keys.
    
    Returns:
    dict: The flattened dictionary.
    """
    items = {}
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten_dict(v, new_key, sep=sep))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    items.update(flatten_dict(item, f"{new_key}{sep}{i}", sep=sep))
            else:
                items[new_key] = v
    elif isinstance(d, list):
        for i, item in enumerate(d):
            items.update(flatten_dict(item, f"{parent_key}{sep}{i}", sep=sep))
    else:
        items[parent_key] = d
    return items

