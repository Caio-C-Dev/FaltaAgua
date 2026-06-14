import re
import unicodedata

from config import (
    CIDADES_GRANDE_BH,
    KEYWORDS_ALERTA,
    KEYWORDS_RETORNO,
    KEYWORDS_NEGATIVAS,
)


def _normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def classify(item: dict) -> dict | None:
    """Returns dict with type, cities, neighborhoods or None if not relevant."""
    raw = f"{item['title']} {item['summary']}"
    text = _normalize(raw)
    text_with_accents = raw.lower()

    if any(neg in text_with_accents for neg in KEYWORDS_NEGATIVAS):
        return None

    has_alerta = any(_normalize(k) in text for k in KEYWORDS_ALERTA)
    has_retorno = any(_normalize(k) in text for k in KEYWORDS_RETORNO)

    if not (has_alerta or has_retorno):
        return None

    cities_found = [c for c in CIDADES_GRANDE_BH if _normalize(c) in text]
    if not cities_found:
        return None

    REGIAO_TERMS = {"grande bh", "regiao metropolitana", "região metropolitana"}
    if any(c in REGIAO_TERMS for c in cities_found):
        cities_found = [
            c for c in CIDADES_GRANDE_BH if c not in REGIAO_TERMS
        ]

    tipo = "RETORNO" if has_retorno else "ALERTA"

    neighborhoods = _extract_neighborhoods(raw)

    return {
        "tipo": tipo,
        "cidades": cities_found,
        "bairros": neighborhoods,
        "titulo": item["title"],
        "link": item["link"],
    }


def _extract_neighborhoods(text: str) -> list[str]:
    """Heuristic: find 'bairro X' or capitalized words after 'bairros'."""
    found = []
    patterns = [
        r"bairros?\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ú\s,]+?)(?:\.|;|\sem\s|\sda\s|\sdo\s|$)",
        r"região\s+d[aoe]\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ú\s]+?)(?:\.|;|,|$)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            chunk = m.group(1).strip()
            for part in re.split(r",|\se\s", chunk):
                part = part.strip()
                if 2 <= len(part.split()) <= 4 or (len(part) > 3 and len(part.split()) == 1):
                    found.append(part.lower())
    return list(set(found))
