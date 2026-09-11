"""Classifica notícias em ALERTA / RETORNO e extrai cidades e bairros.

A comparação de texto é feita sobre a forma "slugificada" (sem acento, sem
pontuação, em minúsculas), a mesma normalização usada pelo app e pelos tópicos
FCM. Isso faz "Ribeirão das Neves", "ribeirao das neves" e "RIBEIRÃO DAS NEVES"
caírem todos no mesmo termo.
"""

import re

from bs4 import BeautifulSoup

from config import (
    APELIDOS_CIDADES,
    CIDADES_CANONICAS,
    MARCADORES_REGIONAIS,
    KEYWORDS_ALERTA,
    KEYWORDS_RETORNO,
    KEYWORDS_NEGATIVAS,
)
from slug import slugify


def _plain_text(html: str) -> str:
    """Remove as tags que o Google News manda dentro do <description>."""
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def _normalize(text: str) -> str:
    """Texto slugificado e delimitado, para casar termos por palavra inteira."""
    return f"_{slugify(text)}_"


def _contains(haystack: str, phrase: str) -> bool:
    """Casamento exato — usado para nomes próprios (cidades, marcadores)."""
    needle = slugify(phrase)
    return bool(needle) and f"_{needle}_" in haystack


# Entre os termos de uma keyword só cabem verbos auxiliares, para que
# "abastecimento SERÁ restabelecido" e "abastecimento JÁ FOI restabelecido"
# casem com "abastecimento restabelecido" — sem abrir espaço para outro
# assunto entrar no meio ("fornecimento DE LUZ restabelecido", "sem
# COMBUSTÍVEL E água"). "não" fica de fora de propósito: inverte o sentido.
_AUXILIARES = (
    "sera", "serao", "foi", "foram", "e", "sao", "esta", "estao",
    "ja", "ainda", "vai", "vao", "deve", "devera", "sendo", "fica", "ficou",
)
# Alternativas mais longas primeiro ("estao" antes de "esta"), para o motor
# não precisar retroceder.
_LACUNA = (
    r"(?:_(?:" + "|".join(sorted(_AUXILIARES, key=len, reverse=True)) + r")){0,2}_"
)


def _compilar(frases: list[str]) -> list[re.Pattern]:
    padroes = []
    for frase in frases:
        termos = [t for t in slugify(frase).split("_") if t]
        if termos:
            padroes.append(re.compile("_" + _LACUNA.join(termos) + "_"))
    return padroes


_RE_ALERTA = _compilar(KEYWORDS_ALERTA)
_RE_RETORNO = _compilar(KEYWORDS_RETORNO)
_RE_NEGATIVA = _compilar(KEYWORDS_NEGATIVAS)


def _matches(padroes: list[re.Pattern], haystack: str) -> bool:
    return any(p.search(haystack) for p in padroes)


def detect_cidades(haystack: str) -> list[str]:
    """Devolve os nomes canônicos das cidades citadas no texto."""
    if any(_contains(haystack, m) for m in MARCADORES_REGIONAIS):
        return list(CIDADES_CANONICAS)

    achadas = {c for c in CIDADES_CANONICAS if _contains(haystack, c)}
    for apelido, cidade in APELIDOS_CIDADES.items():
        if _contains(haystack, apelido):
            achadas.add(cidade)

    return [c for c in CIDADES_CANONICAS if c in achadas]


_BAIRRO_RE = re.compile(
    r"\bbairros?\s+(?:d[aeo]s?\s+)?([^.;:!?()\[\]\n]{2,140})",
    re.IGNORECASE,
)

# Palavras que encerram a enumeração de bairros.
_CORTE_RE = re.compile(
    r"\b(?:além|tamb[ée]m|por[ée]m|mas|desde|durante|ap[óo]s|segundo|conforme|"
    r"informou|informa|afirmou|disse|est[áa]o?|est[aã]o|ficar[aã]m?|ficam|fica|"
    r"seguem?|segue|onde|que|com|sem|at[ée]|para|desta|nesta|no dia|na manh[ãa]|"
    r"na tarde|na noite)\b",
    re.IGNORECASE,
)

_LIGACOES = {"e", "de", "do", "da", "dos", "das", "no", "na", "nos", "nas",
             "em", "o", "a", "os", "as", "à", "às"}

_LIXO = {"", "-", "–", "—"}


def _clean_bairro(part: str) -> str | None:
    tokens = [t for t in part.strip().split() if t]
    while tokens and tokens[0].lower() in _LIGACOES:
        tokens.pop(0)
    if not tokens:
        return None

    nome: list[str] = []
    for token in tokens:
        core = token.strip("\"'“”‘’()[]-–—,.:;!?")
        if core in _LIXO:
            break
        # Nome próprio começa em maiúscula; preposições só valem no meio.
        if core[0].isupper() or (nome and core.lower() in _LIGACOES):
            nome.append(core)
        else:
            break

    while nome and nome[-1].lower() in _LIGACOES:
        nome.pop()

    if not nome or len(nome) > 5:
        return None

    resultado = " ".join(nome)
    return resultado if len(resultado) >= 3 else None


_SEPARADOR_RE = re.compile(r",|\be\b|;|/", re.IGNORECASE)

# "bairros de Belo Horizonte e Contagem" não lista bairros, lista cidades.
_NAO_BAIRRO = (
    {slugify(c) for c in CIDADES_CANONICAS}
    | {slugify(m) for m in MARCADORES_REGIONAIS}
    | {slugify(a) for a in APELIDOS_CIDADES}
)


def extract_bairros(text: str, limite: int = 15) -> list[str]:
    """Extrai bairros de trechos como 'nos bairros Centro, Savassi e Lourdes'.

    O `limite` existe porque o corpo da matéria costuma ter menus e listas de
    notícias relacionadas — sem teto, uma página ruim vira dezenas de falsos
    bairros no Firestore.
    """
    encontrados: list[str] = []
    vistos: set[str] = set()

    for match in _BAIRRO_RE.finditer(text):
        if len(encontrados) >= limite:
            break
        trecho = _CORTE_RE.split(match.group(1))[0]
        for parte in _SEPARADOR_RE.split(trecho):
            nome = _clean_bairro(parte)
            if not nome:
                continue
            chave = slugify(nome)
            if chave in vistos or chave in _NAO_BAIRRO:
                continue
            vistos.add(chave)
            encontrados.append(nome)

    return encontrados


def classify(item: dict) -> dict | None:
    """Converte uma notícia em alerta, ou devolve None se não for relevante."""
    titulo = (item.get("title") or "").strip()
    texto = f"{titulo} {_plain_text(item.get('summary', ''))}".strip()
    if not texto:
        return None

    normalizado = _normalize(texto)

    # ALERTA tem prioridade: quando a notícia menciona os dois ("bairros seguem
    # sem água; abastecimento será restabelecido às 20h"), avisar da falta é mais
    # útil do que anunciar uma normalização que ainda não aconteceu.
    if _matches(_RE_ALERTA, normalizado):
        # Manutenção só anunciada / programada para o futuro não é falta d'água agora.
        if _matches(_RE_NEGATIVA, normalizado):
            return None
        tipo = "ALERTA"
    elif _matches(_RE_RETORNO, normalizado):
        tipo = "RETORNO"
    else:
        return None

    cidades = detect_cidades(normalizado)
    if not cidades:
        return None

    return {
        "tipo": tipo,
        "titulo": titulo,
        "link": item.get("link", ""),
        "cidades": cidades,
        "bairros": extract_bairros(texto),
        "published": item.get("published", ""),
    }
