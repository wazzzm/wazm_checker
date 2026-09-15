import re
import aiohttp
from .base import BaseChecker, CheckResult, Status


class GitHubChecker(BaseChecker):
    name = "GitHub"

    async def check(self, username: str, session: aiohttp.ClientSession) -> CheckResult:
        username = self.normalize(username)

        if not re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username):
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.INVALID,
                message="Неверный формат GitHub username"
            )

        url = f"https://api.github.com/users/{username}"

        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "UsernameCheckerBot/1.0"
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.TAKEN,
                        message=f"Занят ({data.get('name') or data.get('login')})",
                        url=data.get("html_url"),
                        extra={"id": data.get("id"), "type": data.get("type")}
                    )
                elif resp.status == 404:
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.AVAILABLE,
                        message="Свободен",
                        url=f"https://github.com/{username}"
                    )
                else:
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.ERROR,
                        message=f"HTTP {resp.status}"
                    )

        except Exception as e:
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.ERROR,
                message=f"Ошибка: {type(e).__name__}"
            )
