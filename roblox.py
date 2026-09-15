import re
import aiohttp
from .base import BaseChecker, CheckResult, Status


class RobloxChecker(BaseChecker):
    name = "Roblox"

    async def check(self, username: str, session: aiohttp.ClientSession) -> CheckResult:
        username = self.normalize(username)

        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.INVALID,
                message="Неверный формат (3-20 символов, a-z, 0-9, _)"
            )

        # Официальный endpoint проверки
        url = "https://users.roblox.com/v1/usernames/users"
        payload = {
            "usernames": [username],
            "excludeBannedUsers": False
        }

        try:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            ) as resp:
                if resp.status != 200:
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.ERROR,
                        message=f"API ошибка {resp.status}"
                    )

                data = await resp.json()
                users = data.get("data", [])

                if users and len(users) > 0:
                    user = users[0]
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.TAKEN,
                        message=f"Занят (ID: {user.get('id')}, Display: {user.get('displayName', '—')})",
                        url=f"https://www.roblox.com/users/{user.get('id')}/profile",
                        extra={"id": user.get("id"), "displayName": user.get("displayName")}
                    )
                else:
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.AVAILABLE,
                        message="Свободен",
                        url=f"https://www.roblox.com/search/users?keyword={username}"
                    )

        except Exception as e:
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.ERROR,
                message=f"Ошибка: {type(e).__name__}"
            )
