"""Envia notificação fake pra testar o app. Não salva no histórico."""
from notifier import init_firebase, send_push

init_firebase()

fake_alert = {
    "tipo": "ALERTA",
    "titulo": "🧪 TESTE - Falta de água em Belo Horizonte",
    "link": "https://www.otempo.com.br/",
    "cidades": ["belo horizonte"],
    "bairros": ["savassi", "lourdes"],
}

send_push(fake_alert)
print("Push enviado. Confere celular.")
