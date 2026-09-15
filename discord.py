import re
import aiohttp
from .base import BaseChecker, CheckResult, Status


class DiscordChecker(BaseChecker):
    """
    Discord username (pomelo) check is limited without tokens.
    This is a best-effort public check. For accurate results
    you need Discord user tokens (not recommended for production).
    """
    name = "Discord"

    async def check(self, username: str, session: aiohttp.ClientSession) -> CheckResult:
        username = self.normalize(username)

        # Discord usernames: 2-32 chars, lowercase, numbers, underscore, period
        if not re.match(r"^[a-z0-9._]{2,32}$", username):
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.INVALID,
                message="Неверный формат (2-32, a-z, 0-9, ., _)"
            )

        # Публичного надёжного API нет. Можно попробовать через invite-like или другие методы.
        # Здесь делаем заглушку + попытку через известные эндпоинты (могут меняться).

        # Простая проверка через поиск (не очень точная)
        try:
            # Discord не даёт нормального публичного API для этого.
            # Возвращаем UNKNOWN с пояснением.
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.UNKNOWN,
                message="Точная проверка Discord требует токены (ограничено). Попробуй вручную в клиенте.",
                url=f"https://discord.com/users/{username}"  # не работает напрямую
            )
        except Exception as e:
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.ERROR,
                message=str(e)
            )
