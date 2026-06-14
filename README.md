# FaltaAgua

App Flutter + worker Python que monitora notícias de falta de água em Belo Horizonte e região metropolitana. Envia push notification quando a cidade cadastrada do usuário é afetada.

## Stack

- **App:** Flutter 3.41 + Firebase Messaging + Cloud Firestore
- **Worker:** Python 3.11 rodando em GitHub Actions (cron 2/2h)
- **Notícias:** Google News RSS (sem API key)
- **Push:** Firebase Cloud Messaging (topics por cidade)
- **DB:** Firestore (histórico de alertas)
- **Custo total:** R$ 0,00

## Como funciona

```
GitHub Actions (cron 2/2h)
  → Worker Python busca Google News RSS
  → Classifica: ALERTA / RETORNO / ignora
  → Detecta cidades da Grande BH no texto
  → Envia push pro topic FCM da cidade
  → App recebe push (mesmo fechado/sem abrir há meses)
```

## Estrutura

```
FaltaAgua/
├── app/                    # Flutter app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── data/cities.dart           # Cidades da Grande BH
│   │   ├── screens/
│   │   │   ├── setup_screen.dart      # Cadastro cidade + bairro
│   │   │   ├── home_screen.dart       # Tela principal
│   │   │   └── history_screen.dart    # Histórico de alertas
│   │   ├── services/
│   │   │   ├── storage.dart           # SharedPreferences
│   │   │   └── notification_service.dart  # FCM + local notif
│   │   └── utils/slug.dart            # Normaliza nome de cidade
│   └── pubspec.yaml
├── worker/                 # Worker Python
│   ├── main.py             # Entry point
│   ├── config.py           # Cidades + keywords
│   ├── news_fetcher.py     # Google News RSS
│   ├── classifier.py       # ALERTA / RETORNO + extrai bairros
│   ├── notifier.py         # FCM + Firestore dedup
│   ├── slug.py             # Mesma normalização do app
│   └── requirements.txt
├── .github/workflows/
│   └── check_news.yml      # Cron 2/2h
└── README.md
```

## Setup local

### 1. Firebase

1. Cria projeto em [console.firebase.google.com](https://console.firebase.google.com)
2. Add app Android → package `com.aguabh.falta_agua`
3. Baixa `google-services.json` → `app/android/app/google-services.json`
4. Build → Firestore → Create database → modo teste → região `southamerica-east1`
5. Project Settings → Service accounts → Generate new private key → baixa JSON

### 2. App Flutter

```bash
cd app
flutter pub get
flutter run
```

Após primeira tela de histórico abrir, Firestore vai pedir índice composto:
- Collection: `sent_alerts`
- Fields: `cidades_slug` (Array contains), `created_at` (Descending)

### 3. Worker local (teste)

```bash
cd worker
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

# Salva service account JSON como worker/service_account.json
python main.py
```

### 4. GitHub Actions (produção)

1. Push do repo pro GitHub
2. Settings → Secrets and variables → Actions → New repository secret:
   - Name: `FIREBASE_SERVICE_ACCOUNT`
   - Value: conteúdo INTEIRO do `service_account.json`
3. Actions → habilita workflows
4. Workflow roda automático a cada 2 horas

## Cidades monitoradas

Belo Horizonte, Contagem, Betim, Santa Luzia, Ribeirão das Neves, Sabará, Nova Lima, Confins, Ibirité, Vespasiano, Lagoa Santa, Pedro Leopoldo, Caeté.

Quando notícia menciona "Grande BH" ou "Região Metropolitana", alerta é expandido pra todas cidades acima.

## Garantia de entrega de notificação

- **FCM via Google Play Services** entrega push mesmo com app fechado
- **`priority: high`** bypassa Doze mode
- **Battery optimization exemption** (pedido pelo app) impede OEMs (Xiaomi/Samsung) de matar
- **`onTokenRefresh`** atualiza token automático se Google rotacionar

## Licença

MIT
