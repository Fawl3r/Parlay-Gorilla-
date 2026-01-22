from __future__ import annotations

from enum import Enum
from typing import Iterable, Type, TypeVar

StringEnumType = TypeVar("StringEnumType", bound="StringEnum")


class StringEnum(str, Enum):
    @classmethod
    def values(cls: Type[StringEnumType]) -> Iterable[str]:
        return [member.value for member in cls]

    @classmethod
    def from_value(cls: Type[StringEnumType], value: str) -> StringEnumType:
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Invalid {cls.__name__}: {value}")
