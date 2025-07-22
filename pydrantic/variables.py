
from typing import Any
from abc import ABC, abstractmethod
from pydrantic.utils import flatten_dict

class BaseVariable(ABC):
    @abstractmethod
    def resolve(self, data: dict[str, Any]):
        pass

class VariableResolutionError(ValueError):
    pass

class FormatStringVariable(BaseVariable):
    def __init__(self, template: str):
        import re
        self.references = re.findall(r'\{(.*?)\}', template)
        self.template = template.replace("{", "{0[").replace("}", "]}")


    def resolve(self, data: dict[str, Any]) -> str:
        from pydrantic.config import BaseConfig
        data = {k: v.to_dict() if isinstance(v, BaseConfig) else v for k, v in data.items()}
        data = flatten_dict(data, sep=".")
        for k in self.references:
            v = data.get(k)
            if isinstance(v, BaseVariable) and v is not self:
                raise VariableResolutionError(f"Unsupported dependency between Pydrantic variables: {self.template}, {v}")
        return self.template.format(data)
