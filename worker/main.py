"""Entry point do worker.

Fluxo: busca no Google News RSS -> classifica -> abre a matéria para pegar
bairros -> deduplica (por link e por cidade) -> dispara push por tópico.

Variáveis de ambiente:
  FIREBASE_SERVICE_ACCOUNT  JSON completo da service account (usado no CI).
                            Sem ela, cai em worker/service_account.json.
  LOOKBACK_HOURS            Janela de busca em horas (padrão 3). O cron roda a
                            cada 2h, então a sobreposição é proposital — a
                            deduplicação evita push repetido.
  DRY_RUN=1                 Só imprime o que seria enviado; não toca no Firebase.
  MAX_PUSHES                Teto de alertas enviados por execução (padrão 5).
                            Protege contra disparo em massa se alguém rodar
                            com uma janela larga sem o DRY_RUN.
  MAX_ALERTAS               Teto de alertas avaliados por execução (padrão 30).
                            Limita as leituras no Firestore quando uma janela
                            larga traz dezenas de matérias do mesmo evento.
  MAX_ARTIGOS               Quantas matérias abrir por execução para extrair
                            bairros (padrão 10). Cada uma é uma requisição HTTP.
  COOLDOWN_HORAS            Silêncio por (tipo, cidade) — ver notifier.py.
"""

import os
import sys
import traceback

from article import fetch_article_text
from classifier import classify, extract_bairros
from news_fetcher import fetch_recent_news
from notifier import (
    already_sent,
    cidades_fora_de_cooldown,
    init_firebase,
    marcar_cooldown,
    mark_sent,
    send_push,
)

LOOKBACK_HOURS = int(os.environ.get("LOOKBACK_HOURS", "3"))
MAX_PUSHES = int(os.environ.get("MAX_PUSHES", "5"))
MAX_ALERTAS = int(os.environ.get("MAX_ALERTAS", "30"))
MAX_ARTIGOS = int(os.environ.get("MAX_ARTIGOS", "10"))
DRY_RUN = os.environ.get("DRY_RUN", "").strip().lower() in ("1", "true", "yes")


def collect_alerts(hours: int) -> list[dict]:
    noticias = fetch_recent_news(hours)
    print(f"[fetch] {len(noticias)} notícia(s) nas últimas {hours}h")

    alertas: list[dict] = []
    vistos: set[tuple[str, str]] = set()

    for noticia in noticias:
        alerta = classify(noticia)
        if not alerta:
            continue
        chave = (alerta["tipo"], alerta["link"])
        if chave in vistos:
            continue
        vistos.add(chave)
        alertas.append(alerta)

    print(f"[classify] {len(alertas)} alerta(s) relevante(s)")
    return alertas


def enriquecer_bairros(alertas: list[dict], limite: int):
    """Abre a matéria dos ALERTAS para extrair bairros (o RSS não traz corpo)."""
    abertas = 0
    for alerta in alertas:
        if abertas >= limite:
            break
        if alerta["tipo"] != "ALERTA" or alerta["bairros"]:
            continue

        texto = fetch_article_text(alerta["link"])
        abertas += 1
        if texto:
            alerta["bairros"] = extract_bairros(texto)

    if abertas:
        print(f"[article] {abertas} matéria(s) aberta(s) para extrair bairros")


def imprimir(alertas: list[dict]):
    for a in alertas:
        print(f"  [{a['tipo']}] {a['titulo']}")
        print(f"      cidades: {', '.join(a['cidades'])}")
        print(f"      bairros: {', '.join(a['bairros']) or '-'}")
        print(f"      link:    {a['link']}")


def main() -> int:
    alertas = collect_alerts(LOOKBACK_HOURS)
    if not alertas:
        print("Nada a enviar.")
        return 0

    enriquecer_bairros(alertas, MAX_ARTIGOS)
    imprimir(alertas)

    if DRY_RUN:
        print("DRY_RUN ativo — nenhum push enviado.")
        return 0

    try:
        init_firebase()
    except Exception:
        print(
            "[erro] não foi possível inicializar o Firebase. Confira o secret "
            "FIREBASE_SERVICE_ACCOUNT (no CI) ou worker/service_account.json (local).",
            file=sys.stderr,
        )
        raise

    enviados = 0
    repetidos = 0
    silenciados = 0
    falhas = 0

    lote = alertas[:MAX_ALERTAS]
    if len(alertas) > len(lote):
        print(f"[limite] MAX_ALERTAS={MAX_ALERTAS}: avaliando os {len(lote)} primeiros.")

    for processados, alerta in enumerate(lote):
        if enviados >= MAX_PUSHES:
            print(
                f"[limite] MAX_PUSHES={MAX_PUSHES} atingido; "
                f"{len(lote) - processados} alerta(s) não processado(s) "
                "nesta execução."
            )
            break

        try:
            if already_sent(alerta):
                repetidos += 1
                print(f"[skip] já enviado: {alerta['titulo']}")
                continue

            cidades = cidades_fora_de_cooldown(alerta)
            if not cidades:
                silenciados += 1
                # Registra no histórico do app, mas sem push: outro veículo já
                # noticiou o mesmo desabastecimento há pouco.
                mark_sent(alerta, [])
                print(f"[cooldown] sem push: {alerta['titulo']}")
                continue

            send_push(alerta, cidades)
            mark_sent(alerta, cidades)
            marcar_cooldown(alerta, cidades)
            enviados += 1
        except Exception:
            falhas += 1
            print(f"[erro] falha ao processar: {alerta['link']}", file=sys.stderr)
            traceback.print_exc()

    print(
        f"Resumo: {enviados} enviado(s), {repetidos} repetido(s), "
        f"{silenciados} silenciado(s) por cooldown, {falhas} falha(s)."
    )
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
