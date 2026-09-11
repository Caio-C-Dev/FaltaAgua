# FaltaAgua

> **Why I built this:** in my region, the water supply is often cut off and I would only find out late in the day — sometimes I couldn't even shower. So I built this app to know when it happens and prepare for the outage in advance.

A Flutter app + Python worker that monitors news of water supply outages in Belo Horizonte and its metropolitan area. Sends a push notification when the user's registered city is affected.

## Stack

- **App:** Flutter 3.41 + Firebase Messaging + Cloud Firestore
- **Worker:** Python 3.11 running on GitHub Actions (cron every 2 hours)
- **News source:** Google News RSS (no API key required)
- **Push:** Firebase Cloud Messaging (per-city topics)
- **DB:** Firestore (alert history)
- **Total cost:** $0.00

## How it works

```
GitHub Actions (cron every 2h)
  → Python worker fetches Google News RSS
  → Classifies: ALERT / RECOVERY / ignore
  → Detects Greater BH cities in the text
  → Sends push to the city's FCM topic
  → App receives push (even when closed or unopened for months)
```

## Project structure

```
FaltaAgua/
├── app/                    # Flutter app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── data/cities.dart           # Greater BH cities
│   │   ├── screens/
│   │   │   ├── setup_screen.dart      # City + neighborhood registration
│   │   │   ├── home_screen.dart       # Main screen
│   │   │   └── history_screen.dart    # Alert history
│   │   ├── services/
│   │   │   ├── storage.dart           # SharedPreferences
│   │   │   └── notification_service.dart  # FCM + local notif
│   │   └── utils/slug.dart            # City name normalization
│   └── pubspec.yaml
├── worker/                 # Python worker
│   ├── main.py             # Entry point
│   ├── config.py           # Cities + keywords
│   ├── news_fetcher.py     # Google News RSS
│   ├── classifier.py       # ALERT / RECOVERY + neighborhood extraction
│   ├── article.py          # Fetches article body (RSS has no text)
│   ├── notifier.py         # FCM + Firestore deduplication
│   ├── slug.py             # Same normalization as the app
│   └── requirements.txt
├── .github/workflows/
│   └── check_news.yml      # Cron every 2 hours
└── README.md
```

## Local setup

### 1. Firebase

1. Create a project at [console.firebase.google.com](https://console.firebase.google.com)
2. Add an Android app → package `com.aguabh.falta_agua`
3. Download `google-services.json` → `app/android/app/google-services.json`
4. Build → Firestore → Create database → test mode → region `southamerica-east1`
5. Project Settings → Service accounts → Generate new private key → download JSON

### 2. Flutter app

```bash
cd app
flutter pub get
flutter run
```

The first time the history screen opens, Firestore will ask for a composite index:
- Collection: `sent_alerts`
- Fields: `cidades_slug` (Array contains), `created_at` (Descending)

### 3. Worker (local test)

```bash
cd worker
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt

# Save the service account JSON as worker/service_account.json
python main.py

# Classify only, without sending push or touching Firebase:
DRY_RUN=1 python main.py          # PowerShell: $env:DRY_RUN=1; python main.py

# Widen the search window (default: 3 hours):
LOOKBACK_HOURS=48 DRY_RUN=1 python main.py
```

### 4. GitHub Actions (production)

1. Push the repo to GitHub
2. Settings → Secrets and variables → Actions → New repository secret:
   - Name: `FIREBASE_SERVICE_ACCOUNT`
   - Value: the FULL contents of `service_account.json`
3. Actions → enable workflows
4. The workflow runs automatically every 2 hours
5. To test by hand: Actions → Check Water Outage News → Run workflow. The
   `dry_run` input classifies and logs without sending any push, and
   `lookback_hours` widens the search window.

## Deduplication

The same outage is typically covered by four or five outlets, so deduplication
happens at two levels:

- **By link** (`sent_alerts`) — the same article is never processed twice.
- **By event** (`alert_cooldown`) — after notifying a city, that city stays
  silent for `COOLDOWN_HORAS` (default 12) for that alert type. The other
  outlets' articles still land in the history, but send no push.

`MAX_PUSHES` (default 5) caps how many alerts a single run may send, so a wide
`LOOKBACK_HOURS` without `DRY_RUN` can't flood everyone's phone.

## Monitored cities

Belo Horizonte, Contagem, Betim, Santa Luzia, Ribeirão das Neves, Sabará, Nova Lima, Confins, Ibirité, Vespasiano, Lagoa Santa, Pedro Leopoldo, Caeté.

When a news article mentions "Grande BH" or "Região Metropolitana", the alert is expanded to all cities above.

## Delivery guarantees

- **FCM via Google Play Services** delivers push even when the app is closed
- **`priority: high`** bypasses Doze mode
- **Battery optimization exemption** (requested by the app) prevents OEMs (Xiaomi, Samsung) from killing the service
- **`onTokenRefresh`** updates the token automatically if Google rotates it

## License

MIT
