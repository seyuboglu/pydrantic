from __future__ import annotations
import yaml
from typing import Any, Dict, List, Optional, Type, Union
from abc import abstractmethod

from pathlib import Path
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic import Field, model_validator

from pydrantic.utils import type_from_dict, save_dill, save_pickle, import_object, type_to_dict, unflatten_dict, flatten_dict, load_dill, load_pickle
from pydrantic.variables import BaseVariable, VariableResolutionError


MAX_RESOLUTION_DEPTH = 5

class BaseConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_default=True,
        protected_namespaces=('model_validate', 'model_dump',)
    )
    _variables: Optional[Dict[str, BaseVariable]] = None

    @model_validator(mode="wrap")
    def resolve_variables(cls, values: dict[str, Any], handler) -> dict[str, Any]:
        if isinstance(values, BaseConfig):
            return handler(values)
        
        variables = {}
        for _ in range(MAX_RESOLUTION_DEPTH):
            variables_remaining = False
            for k, v in values.items():
                if isinstance(v, BaseVariable):
                    try:
                        values[k] = v.resolve(values)
                    except VariableResolutionError as e:
                        variables_remaining = True
                    else:
                        variables[k] = v
            if not variables_remaining:
                break
        else:
            raise VariableResolutionError(f"Max resolution depth reached for {values}")
            

        config: BaseConfig = handler(values)
        config._variables = variables
        return config
    
    def get(self, key, default=None):
        return getattr(self, key, default)

    def to_dict(self):
        return self._to_dict(self)
    
    def _to_dict(self, obj: any):
        if isinstance(obj, BaseConfig):
            data = {
                "_config_type": type_to_dict(type(obj))
            }
            for k, v in obj:
                data[k] = self._to_dict(v)
            return data
        elif isinstance(obj, type):
            return type_to_dict(obj)
        elif isinstance(obj, list):
            return [self._to_dict(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self._to_dict(v) for k, v in obj.items()}
        else:
            return obj        
    

    @classmethod
    def from_dict(cls, data: Dict, strict: bool = True):
        if "_config_type" in data:
            if isinstance(data["_config_type"], dict):
                cls = type_from_dict(data["_config_type"])
            else:
                # SE (12/14): Backwards compatibility for old configs before support for inner classes
                cls = import_object(data["_config_type"])

        def _is_config(v):
            return isinstance(v, dict) and "_config_type" in v
    
        def _is_type(v):
            return isinstance(v, dict) and "_is_type" in v
        
        result = {}
        for k, v in data.items():
            if k == "_config_type":
                continue
            if _is_config(v):
                result[k] = cls.from_dict(v, strict=strict)
            elif _is_type(v):
                result[k] = type_from_dict(v)
            elif isinstance(v, list):
                result[k] = [cls.from_dict(i, strict=strict) if _is_config(i) else i for i in v]
            elif isinstance(v, dict):
                result[k] = {k: cls.from_dict(v, strict=strict) if _is_config(v) else v for k, v in v.items()}
            else:
                result[k] = v

        if any(k not in cls.model_fields for k in result.keys()):
            if strict:
                raise ValueError(f"Missing fields: {', '.join(k for k in result.keys() if k not in cls.model_fields)}")
            else:
                print(f"Missing fields: {', '.join(k for k in result.keys() if k not in cls.model_fields)}")
                result = {k: v for k, v in result.items() if k in cls.model_fields}
        return cls.model_validate(result, strict=strict)
    
    def to_yaml(self, path: str):
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f)

    @classmethod
    def from_yaml(cls, path: str, strict: bool = True):
        with open(path, "r") as f:
            data = yaml.load(f, Loader=yaml.CLoader)
        return cls.from_dict(data, strict=strict)

    def to_dill(self, path: str):
        save_dill(self.to_dict(), path)
    
    @classmethod
    def from_dill(cls, path: str, strict: bool = True):
        return cls.from_dict(load_dill(path), strict=strict)
    
    def to_pickle(self, path: str):
        save_pickle(self.to_dict(), path)
    
    @classmethod
    def from_pickle(cls, path: str, strict: bool = True):
        return cls.from_dict(load_pickle(path), strict=strict)
        
    @classmethod
    def from_wandb(cls, run_id: str, strict: bool = True):
        """
        Load a config from a wandb run ID.
    
        Parameters:
            run_id (str): A full wandb run id like "hazy-research/attention/159o6asi"
        """
        import wandb

        # 1: Get configuration from wandb
        api = wandb.Api()
        run = api.run(run_id)
        config = unflatten_dict(run.config)
        
        if "callbacks" in config and len(config["callbacks"]) > 0 and isinstance(config["callbacks"][0], str):
            # SE (04/01): this is a hack to deal with a bug in an old version of 
            # to_dict that didn't work with lists
            # eventually this can be removed when all configs are updated
            config["callbacks"] = []

        return cls.from_dict(config, strict=strict)

    def print(self):
        try:
            import rich
            rich.print(self)
        except ImportError:
            print(self)

    def flatten(self):
        return flatten_dict(self.to_dict())
        


class RunConfig(BaseConfig):
    run_dir: Optional[str] = None
    output_dir: Optional[str] = None
    run_id: Optional[str] = None

    # unique id for the 
    launch_id: Optional[str] = None

    # a
    script_id: Optional[str] = None

    @abstractmethod
    def run(self):
        raise NotImplementedError("`run` must be implemented in subclasses of `RunConfig`.")



class ObjectConfig(BaseConfig):
    target: Union[Type, str, None] = None
    kwargs: Optional[Dict] = Field(default_factory=dict)
    _pass_as_config: bool = False

    @field_validator("target", mode="before")
    def infer_target(cls, v, values):
        if v is None:
            parts = cls.__qualname__.split(".")
            if len(parts) < 2:
                raise ValueError(f"Cannot infer target for {cls.__qualname__}")
            elif len(parts) == 2:
                v = import_object(cls.__module__ + "." + parts[0])
            else:
                raise ValueError(f"Cannot infer target for {cls.__qualname__}")
        return v
     

    def instantiate(self, *args, **kwargs):
        if isinstance(self.target, str):
            target = import_object(self.target)
        else:
            target = self.target
        if self._pass_as_config:
            return target(self, *args, **self.kwargs, **kwargs)
        # kwargs will overwrite the fields in the config
        return target(
            *args,
            **self.kwargs,
            **kwargs,
            **self.model_dump(exclude={"target", "kwargs"} | set(kwargs.keys())),
        )


def get_unique_ids(
    configs: List[BaseConfig], 
    exclude: List[str] = [],
    sep: str = "."
) -> List[str]:
    flattened_configs = [flatten_dict(config.to_dict(), sep=sep) for config in configs]

    differing_keys = set()
    all_keys = set([key for config in flattened_configs for key in config.keys()])
    for key in all_keys:
        if key in exclude:
            continue
        values = set()
        for config in flattened_configs:
            if key in config:
                values.add(config[key])
        if len(values) > 1:
            differing_keys.add(key)

    unique_ids = []
    for config in flattened_configs:
        id_parts = [
            f"{key.split('.')[-1]}={config[key]}" 
            for key in differing_keys 
            if key in config
        ]
        unique_id = '-'.join(id_parts)
        unique_ids.append(unique_id)

    return unique_ids