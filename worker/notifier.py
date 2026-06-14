import os
import json
import hashlib

import firebase_admin
from firebase_admin import credentials, firestore, messaging

from slug import slugify, city_topic


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


def mark_sent(alert: dict):
    db = firestore.client()
    h = _alert_hash(alert)
    db.collection("sent_alerts").document(h).set({
        "tipo": alert["tipo"],
        "link": alert["link"],
        "titulo": alert["titulo"],
        "cidades": alert["cidades"],
        "cidades_slug": [slugify(c) for c in alert["cidades"]],
        "bairros": alert["bairros"],
        "created_at": firestore.SERVER_TIMESTAMP,
    })


def send_push(alert: dict):
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

    for city in alert["cidades"]:
        topic = city_topic(city)
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data,
            topic=topic,
            android=android_cfg,
        )
        msg_id = messaging.send(msg)
        print(f"Push sent to topic {topic}: {msg_id}")
