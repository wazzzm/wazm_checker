from .telegram import TelegramChecker
from .roblox import RobloxChecker
from .github import GitHubChecker
from .steam import SteamChecker
from .minecraft import MinecraftChecker
from .discord import DiscordChecker
from .base import CheckResult, Status

ALL_CHECKERS = [
    TelegramChecker(),
    RobloxChecker(),
    GitHubChecker(),
    SteamChecker(),
    MinecraftChecker(),
    # DiscordChecker(),  # пока отключен из-за ограничений API
]

PLATFORM_MAP = {c.name.lower(): c for c in ALL_CHECKERS}
