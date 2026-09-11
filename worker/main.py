"""Entry point do worker.

Fluxo: busca no Google News RSS -> classifica -> deduplica no Firestore ->
dispara push por tópico de cidade.

Variáveis de ambiente:
  FIREBASE_SERVICE_ACCOUNT  JSON completo da service account (usado no CI).
                            Sem ela, cai em worker/service_account.json.
  LOOKBACK_HOURS            Janela de busca em horas (padrão 3). O cron roda a
                            cada 2h, então a sobreposição é proposital — a
                            deduplicação no Firestore evita push repetido.
  DRY_RUN=1                 Só imprime o que seria enviado; não toca no Firebase.
"""

import os
import sys
import traceback

from classifier import classify
from news_fetcher import fetch_recent_news
from notifier import already_sent, init_firebase, mark_sent, send_push

LOOKBACK_HOURS = int(os.environ.get("LOOKBACK_HOURS", "3"))
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


def main() -> int:
    alertas = collect_alerts(LOOKBACK_HOURS)

    for a in alertas:
        bairros = ", ".join(a["bairros"]) or "-"
        print(f"  [{a['tipo']}] {a['titulo']}")
        print(f"      cidades: {', '.join(a['cidades'])}")
        print(f"      bairros: {bairros}")
        print(f"      link:    {a['link']}")

    if not alertas:
        print("Nada a enviar.")
        return 0

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
    falhas = 0

    for alerta in alertas:
        try:
            if already_sent(alerta):
                repetidos += 1
                print(f"[skip] já enviado: {alerta['titulo']}")
                continue
            send_push(alerta)
            mark_sent(alerta)
            enviados += 1
        except Exception:
            falhas += 1
            print(f"[erro] falha ao processar: {alerta['link']}", file=sys.stderr)
            traceback.print_exc()

    print(f"Resumo: {enviados} enviado(s), {repetidos} repetido(s), {falhas} falha(s).")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
