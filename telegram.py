import re
import aiohttp
from .base import BaseChecker, CheckResult, Status


class TelegramChecker(BaseChecker):
    name = "Telegram"

    async def check(self, username: str, session: aiohttp.ClientSession) -> CheckResult:
        username = self.normalize(username)

        # Валидация правил Telegram
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]{4,31}$", username):
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.INVALID,
                message="Неверный формат (5-32 символа, начинается с буквы, только a-z, 0-9, _)"
            )

        url = f"https://t.me/{username}"

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout), allow_redirects=True) as resp:
                text = await resp.text()
                final_url = str(resp.url)

                # Если редирект на t.me/username и страница содержит признаки существующего аккаунта
                if "tgme_page_title" in text or "tgme_page_photo" in text or "tgme_page_description" in text:
                    # Дополнительно проверяем, не "If you have Telegram, you can contact..."
                    if "If you have <strong>Telegram</strong>, you can contact" in text or "tgme_username_link" in text:
                        # Часто это признак существующего
                        return CheckResult(
                            platform=self.name,
                            username=username,
                            status=Status.TAKEN,
                            message="Занят",
                            url=url
                        )
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.TAKEN,
                        message="Занят (аккаунт/канал/бот существует)",
                        url=url
                    )

                # Страница "username not found" / "If you have Telegram..."
                if "tgme_page_icon" in text and "If you have" in text:
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.AVAILABLE,
                        message="Свободен (приблизительно)",
                        url=url
                    )

                # Fallback по статусу
                if resp.status == 200:
                    # Безопаснее считать занятым, если страница открылась
                    return CheckResult(
                        platform=self.name,
                        username=username,
                        status=Status.TAKEN,
                        message="Скорее всего занят",
                        url=url
                    )

                return CheckResult(
                    platform=self.name,
                    username=username,
                    status=Status.UNKNOWN,
                    message=f"Не удалось точно определить (HTTP {resp.status})",
                    url=url
                )

        except Exception as e:
            return CheckResult(
                platform=self.name,
                username=username,
                status=Status.ERROR,
                message=f"Ошибка сети: {type(e).__name__}"
            )
