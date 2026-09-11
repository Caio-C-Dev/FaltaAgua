"""Busca o corpo da matéria para extrair bairros.

O RSS do Google News só entrega título e link — nenhum texto útil. Para saber
quais bairros foram citados é preciso abrir a página da notícia.

Os links do RSS apontam para news.google.com e redirecionam para o veículo.
Às vezes o redirecionamento é HTTP (o requests segue sozinho), às vezes vem
uma página-ponte com o link real no HTML; por isso o fallback abaixo.

Tudo aqui é best-effort: qualquer falha devolve string vazia e o alerta segue
sem bairros, que é exatamente o comportamento de antes.
"""

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

TIMEOUT = 10
MAX_CHARS = 8000
MAX_BYTES = 2_000_000  # teto de download: página de jornal é pesada de banner

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}

_RUIDO = ["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]

# Domínios que aparecem na página-ponte mas nunca são a matéria.
_NAO_MATERIA = (
    "google.com", "gstatic.com", "youtube.com", "facebook.com", "twitter.com",
    "x.com", "instagram.com", "linkedin.com", "whatsapp.com", "t.me",
    "play.google.com", "apps.apple.com",
)


def _e_materia(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return bool(host) and not any(host.endswith(d) or host == d for d in _NAO_MATERIA)


def _rel_canonical(valor) -> bool:
    """O bs4 entrega `rel` como lista, por ser atributo multivalorado."""
    if not valor:
        return False
    itens = valor if isinstance(valor, list) else [valor]
    return any(str(item).lower() == "canonical" for item in itens)


def _absolutizar(href: str, base: str) -> str:
    """Resolve href relativo ("/noticia/123") contra a URL da página."""
    return urljoin(base, href.strip()) if href else ""


def _link_real(soup: BeautifulSoup, base: str) -> str | None:
    """Extrai o destino de uma página-ponte do Google News.

    Ordem de preferência: canonical e og:url são declarações explícitas da
    página sobre si mesma; a varredura de <a> é o último recurso, porque lá
    aparecem também links de rede social e de navegação.
    """
    canonical = soup.find("link", rel=_rel_canonical)
    if canonical and canonical.get("href"):
        destino = _absolutizar(canonical["href"], base)
        if _e_materia(destino):
            return destino

    og = soup.find("meta", attrs={"property": "og:url"})
    if og and og.get("content"):
        destino = _absolutizar(og["content"], base)
        if _e_materia(destino):
            return destino

    meta = soup.find("meta", attrs={"http-equiv": re.compile("refresh", re.I)})
    if meta and meta.get("content"):
        achado = re.search(r"url=(.+)", meta["content"], re.I)
        if achado:
            destino = _absolutizar(achado.group(1).strip("'\" "), base)
            if _e_materia(destino):
                return destino

    # O Google marca o link da matéria com data-n-au na página-ponte.
    marcado = soup.find("a", attrs={"data-n-au": True})
    if marcado and marcado.get("href"):
        destino = _absolutizar(marcado["href"], base)
        if _e_materia(destino):
            return destino

    for a in soup.find_all("a", href=True):
        destino = _absolutizar(a["href"], base)
        if _e_materia(destino):
            return destino

    return None


def _baixar(url: str) -> tuple[str, str]:
    """Devolve (html, url_final). HTML vazio se não for página HTML."""
    resp = requests.get(
        url, timeout=TIMEOUT, headers=_HEADERS, allow_redirects=True, stream=True
    )
    try:
        resp.raise_for_status()
        if "html" not in resp.headers.get("Content-Type", "").lower():
            return "", resp.url

        bruto = bytearray()
        for pedaco in resp.iter_content(8192):
            bruto += pedaco
            if len(bruto) >= MAX_BYTES:
                break

        return bytes(bruto).decode(resp.encoding or "utf-8", errors="replace"), resp.url
    finally:
        resp.close()


def fetch_article_text(url: str, _profundidade: int = 0) -> str:
    """Devolve o texto limpo da matéria, ou "" se não der para buscar."""
    if not url or _profundidade > 1:
        return ""

    try:
        html, url_final = _baixar(url)
    except requests.RequestException as exc:
        print(f"[article] falha ao buscar {url[:80]}...: {exc}")
        return ""

    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    if "news.google.com" in url_final:
        destino = _link_real(soup, url_final)
        return fetch_article_text(destino, _profundidade + 1) if destino else ""

    for tag in soup(_RUIDO):
        tag.decompose()

    corpo = soup.find("article") or soup.body or soup
    return corpo.get_text(" ", strip=True)[:MAX_CHARS]
