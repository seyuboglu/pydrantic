
from typing import Any
from abc import ABC, abstractmethod
from pydrantic.utils import flatten_dict

class BaseVariable(ABC):
    @abstractmethod
    def resolve(self, data: dict[str, Any]):
        pass

class FormatStringVariable(BaseVariable):
    def __init__(self, template: str):
        self.template = template.replace("{", "{0[").replace("}", "]}")

    def resolve(self, data: dict[str, Any]) -> str:
        from pydrantic.config import BaseConfig
        data = {k: v.to_dict() if isinstance(v, BaseConfig) else v for k, v in data.items()}
        data = flatten_dict(data, sep=".")        
        return self.template.format(data)
