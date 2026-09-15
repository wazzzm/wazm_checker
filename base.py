from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import aiohttp


class Status(str, Enum):
    AVAILABLE = "available"
    TAKEN = "taken"
    INVALID = "invalid"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    platform: str
    username: str
    status: Status
    message: str = ""
    url: Optional[str] = None
    extra: Optional[dict] = None


class BaseChecker(ABC):
    name: str = "base"
    timeout: float = 10.0

    @abstractmethod
    async def check(self, username: str, session: aiohttp.ClientSession) -> CheckResult:
        pass

    def normalize(self, username: str) -> str:
        return username.strip().lstrip("@").lower()
