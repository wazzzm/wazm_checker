import re
import aiohttp
from .base import BaseChecker, CheckResult, Status


class SteamChecker(BaseChecker):
    name = "Steam"

    async def check(self, username: str, session: aiohttp.ClientSession) -> CheckResult:
        username = self.normalize(username)

        # Steam vanity URL: 2-32 символа
        if not re.match(r"^[a-zA-Z0-9_-]{2,32}$", username):
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.INVALID,
                message="Неверный формат (2-32 символа)"
            )

        # Проверяем через vanity URL resolve (публичный)
        url = f"https://steamcommunity.com/id/{username}"

        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"}
            ) as resp:
                text = await resp.text()
                final = str(resp.url)

                # Если редирект на /profiles/XXXX — значит vanity занят
                if "/profiles/" in final and username.lower() not in final.lower():
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.TAKEN,
                        message="Занят (vanity URL)",
                        url=final
                    )

                if "The specified profile could not be found" in text or "profile could not be found" in text.lower():
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.AVAILABLE,
                        message="Свободен (vanity)",
                        url=url
                    )

                # Страница профиля существует
                if "steamID" in text or "profile_header" in text or "playerAvatar" in text:
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.TAKEN,
                        message="Занят",
                        url=final
                    )

                return CheckResult(
                    platform=self.name,
                    username=username,
                    status=Status.UNKNOWN,
                    message="Не удалось точно определить",
                    url=url
                )

        except Exception as e:
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.ERROR,
                message=f"Ошибка: {type(e).__name__}"
            )
