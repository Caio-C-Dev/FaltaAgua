import re
import unicodedata


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def city_topic(city: str) -> str:
    return f"cidade_{slugify(city)}"
