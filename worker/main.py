from news_fetcher import fetch_recent_news
from classifier import classify
from notifier import init_firebase, already_sent, mark_sent, send_push


def run():
    print("Fetching news...")
    news = fetch_recent_news(hours=3)
    print(f"Found {len(news)} recent items")

    init_firebase()

    for item in news:
        alert = classify(item)
        if not alert:
            continue

        print(f"[{alert['tipo']}] {alert['titulo']}")
        print(f"  Cidades: {alert['cidades']}")
        print(f"  Bairros: {alert['bairros']}")

        if already_sent(alert):
            print("  Already sent, skipping")
            continue

        send_push(alert)
        mark_sent(alert)


if __name__ == "__main__":
    run()
