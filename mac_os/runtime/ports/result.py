"""Provider-independent capability outcomes. No vendor exceptions or payloads."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar, Union

T = TypeVar("T")


class ErrorCode(StrEnum):
    INVALID_INPUT = "invalid_input"
    INVALID_RESPONSE = "invalid_response"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    INFERENCE_FAILED = "inference_failed"


@dataclass(frozen=True)
class Success(Generic[T]):
    value: T


@dataclass(frozen=True)
class Failure:
    error: ErrorCode


Result = Union[Success[T], Failure]
