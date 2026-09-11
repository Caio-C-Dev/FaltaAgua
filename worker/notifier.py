import os
import json
import hashlib
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import credentials, firestore, messaging

from slug import slugify, city_topic

# Janela de silêncio por (tipo, cidade). O mesmo desabastecimento costuma ser
# coberto por 4 ou 5 veículos; sem isso, cada matéria vira uma notificação.
COOLDOWN_HORAS = int(os.environ.get("COOLDOWN_HORAS", "12"))


def init_firebase():
    if firebase_admin._apps:
        return
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if sa_json:
        cred = credentials.Certificate(json.loads(sa_json))
    else:
        cred = credentials.Certificate("service_account.json")
    firebase_admin.initialize_app(cred)


def _alert_hash(alert: dict) -> str:
    key = f"{alert['tipo']}|{alert['link']}"
    return hashlib.sha256(key.encode()).hexdigest()


def already_sent(alert: dict) -> bool:
    db = firestore.client()
    h = _alert_hash(alert)
    doc = db.collection("sent_alerts").document(h).get()
    return doc.exists


def _cooldown_id(tipo: str, cidade: str) -> str:
    return f"{tipo.lower()}_{slugify(cidade)}"


def cidades_fora_de_cooldown(alert: dict) -> list[str]:
    """Filtra as cidades que já receberam esse tipo de aviso há pouco tempo.

    Lê as cidades de uma vez só: uma notícia da Grande BH expande para 13
    cidades, e 13 idas separadas ao Firestore por alerta somam rápido.
    """
    if not alert["cidades"]:
        return []

    db = firestore.client()
    limite = datetime.now(timezone.utc) - timedelta(hours=COOLDOWN_HORAS)
    colecao = db.collection("alert_cooldown")

    por_id = {_cooldown_id(alert["tipo"], c): c for c in alert["cidades"]}
    snapshots = db.get_all([colecao.document(doc_id) for doc_id in por_id])

    em_silencio = set()
    for snap in snapshots:
        if not snap.exists:
            continue
        ultimo = (snap.to_dict() or {}).get("last_sent")
        if ultimo and ultimo > limite:
            em_silencio.add(snap.id)

    return [cidade for doc_id, cidade in por_id.items() if doc_id not in em_silencio]


def marcar_cooldown(alert: dict, cidades: list[str]):
    if not cidades:
        return

    db = firestore.client()
    lote = db.batch()
    for cidade in cidades:
        ref = db.collection("alert_cooldown").document(
            _cooldown_id(alert["tipo"], cidade)
        )
        lote.set(ref, {
            "tipo": alert["tipo"],
            "cidade": cidade,
            "cidade_slug": slugify(cidade),
            "ultimo_link": alert["link"],
            "last_sent": firestore.SERVER_TIMESTAMP,
        })
    lote.commit()


def mark_sent(alert: dict, cidades_notificadas: list[str] | None = None):
    db = firestore.client()
    h = _alert_hash(alert)
    db.collection("sent_alerts").document(h).set({
        "tipo": alert["tipo"],
        "link": alert["link"],
        "titulo": alert["titulo"],
        "cidades": alert["cidades"],
        "cidades_slug": [slugify(c) for c in alert["cidades"]],
        "bairros": alert["bairros"],
        # Vazio quando a matéria foi engolida pelo cooldown: fica no histórico
        # do app, mas não gerou push.
        "cidades_notificadas": (
            alert["cidades"] if cidades_notificadas is None else cidades_notificadas
        ),
        "created_at": firestore.SERVER_TIMESTAMP,
    })


def send_push(alert: dict, cidades: list[str] | None = None):
    tipo = alert["tipo"]
    icon = "🚨" if tipo == "ALERTA" else "✅"
    title = f"{icon} {'ALERTA' if tipo == 'ALERTA' else 'NORMALIZADO'} - Falta de Água"
    body = alert["titulo"]

    android_cfg = messaging.AndroidConfig(
        priority="high",
        notification=messaging.AndroidNotification(
            channel_id="falta_agua_channel",
            sound="default",
        ),
    )
    data = {"link": alert["link"], "tipo": tipo}

    for city in (alert["cidades"] if cidades is None else cidades):
        topic = city_topic(city)
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data,
            topic=topic,
            android=android_cfg,
        )
        msg_id = messaging.send(msg)
        print(f"Push sent to topic {topic}: {msg_id}")
