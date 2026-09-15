import aiohttp
import os
import re
from typing import List


async def generate_usernames(
    prompt: str,
    count: int = 8,
    style: str = "any"
) -> List[str]:
    """
    Генерирует варианты юзернеймов с помощью LLM.
    Если AI_API_KEY не задан — использует rule-based fallback.
    """
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_API_BASE", "https://api.groq.com/openai/v1")
    model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

    if not api_key:
        return _rule_based(prompt, count)

    system = (
        "You are a creative username generator. "
        "Generate short, available-looking usernames based on the user request. "
        "Rules: only lowercase latin letters, numbers and underscore. "
        "Length 4-16 characters. No spaces. Return ONLY a JSON array of strings, nothing else."
    )

    user_msg = f"Generate {count} usernames. Request: {prompt}. Style preference: {style}."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.9,
        "max_tokens": 300
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                if resp.status != 200:
                    return _rule_based(prompt, count)

                data = await resp.json()
                content = data["choices"][0]["message"]["content"].strip()

                # Пытаемся вытащить JSON массив
                match = re.search(r"\[.*\]", content, re.DOTALL)
                if match:
                    import json
                    names = json.loads(match.group(0))
                    cleaned = []
                    for n in names:
                        n = re.sub(r"[^a-z0-9_]", "", str(n).lower())
                        if 4 <= len(n) <= 16:
                            cleaned.append(n)
                    return cleaned[:count] if cleaned else _rule_based(prompt, count)

                return _rule_based(prompt, count)
    except Exception:
        return _rule_based(prompt, count)


def _rule_based(prompt: str, count: int) -> List[str]:
    """Простой fallback без AI"""
    base = re.sub(r"[^a-z0-9]", "", prompt.lower())[:8] or "user"
    suffixes = ["", "_x", "1", "42", "pro", "hq", "io", "dev", "gg", "hub", "lab", "zone"]
    prefixes = ["", "the", "get", "my", "real", "its"]

    results = []
    for p in prefixes:
        for s in suffixes:
            name = f"{p}{base}{s}" if p else f"{base}{s}"
            name = name[:16]
            if 4 <= len(name) <= 16 and name not in results:
                results.append(name)
            if len(results) >= count:
                return results
    return results[:count]
