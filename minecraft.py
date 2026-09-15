import re
import aiohttp
from .base import BaseChecker, CheckResult, Status


class MinecraftChecker(BaseChecker):
    name = "Minecraft"

    async def check(self, username: str, session: aiohttp.ClientSession) -> CheckResult:
        username = self.normalize(username)

        if not re.match(r"^[a-zA-Z0-9_]{3,16}$", username):
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.INVALID,
                message="Неверный формат (3-16 символов, a-z, 0-9, _)"
            )

        # Можем использовать официальный Mojang API (устарел, но работает для проверки)
        # Лучше NameMC или Ashcon
        url = f"https://api.mojang.com/users/profiles/minecraft/{username}"

        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"User-Agent": "UsernameCheckerBot/1.0"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    uuid = data.get("id")
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.TAKEN,
                        message=f"Занят (UUID: {uuid})",
                        url=f"https://namemc.com/profile/{username}",
                        extra={"uuid": uuid}
                    )
                elif resp.status == 204 or resp.status == 404:
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.AVAILABLE,
                        message="Свободен",
                        url=f"https://namemc.com/search?q={username}"
                    )
                else:
                    # Fallback на NameMC
                    return await self._check_namemc(username, session)

        except Exception:
            return await self._check_namemc(username, session)

    async def _check_namemc(self, username: str, session: aiohttp.ClientSession) -> CheckResult:
        url = f"https://api.namemc.com/profile/{username}"  # может не работать, используем страницу
        page_url = f"https://namemc.com/search?q={username}"

        try:
            async with session.get(
                page_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"User-Agent": "Mozilla/5.0"}
            ) as resp:
                text = await resp.text()
                if "No results found" in text or "0 results" in text.lower():
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.AVAILABLE,
                        message="Свободен (по NameMC)",
                        url=page_url
                    )
                # Если есть карточки профилей
                if "card-title" in text or username.lower() in text.lower():
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.TAKEN,
                        message="Скорее всего занят",
                        url=f"https://namemc.com/profile/{username}"
                    )
                return CheckResult(
                    platform=self.name,
                    username=username,
                    status=Status.UNKNOWN,
                    message="Не удалось определить",
                    url=page_url
                )
        except Exception as e:
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.ERROR,
                message=f"Ошибка: {type(e).__name__}"
            )
