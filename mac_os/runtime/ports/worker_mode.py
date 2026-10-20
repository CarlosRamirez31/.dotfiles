"""Private worker protocol modes, independent from model providers."""

from enum import StrEnum


class WorkerMode(StrEnum):
    ENROLL = "enroll"
    STREAM = "stream"
