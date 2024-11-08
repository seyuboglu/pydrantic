from typing import Any
from pydantic import ValidationInfo, GetCoreSchemaHandler
from pydantic import Field
from pydantic_core import core_schema
import string
from typing_extensions import Annotated


class FormatStr(Annotated[str, Field(validate_default=True)]):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, info: ValidationInfo):
        if not isinstance(v, str):
            raise TypeError('string required')
        try:
            return v.format(**info.data)
        except KeyError as e:
            raise ValueError(f"Invalid field in format string: {e}")
        
