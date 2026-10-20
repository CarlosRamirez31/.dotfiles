"""Capability boundary; no model SDK or transport types."""

from typing import Protocol

from ports.result import Result


class PersonalVoiceAdapter(Protocol):
    def set_embedding(self, pcm: bytes) -> Result[None]: ...
    def enroll(self, pcm: bytes) -> Result[list[float]]: ...
    def probability(self, pcm: bytes) -> Result[float]: ...
