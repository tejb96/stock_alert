# Gold/Silver ratio alerts

FastAPI service that polls Yahoo Finance futures (`GC=F`, `SI=F`), computes the gold/silver ratio, and sends **Discord** alerts when a threshold is **crossed** (one notification per cross, no repeat spam while the ratio stays above/below).

## Setup

```bash
cd backend
cp .env.example .env
# Edit .env and set DISCORD_WEBHOOK_URL
uv run fastapi dev app.main:app
```

Create a Discord webhook: Server → Channel → Integrations → Webhooks → New Webhook → copy URL into `DISCORD_WEBHOOK_URL`.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ratio` | Current ratio and prices |
| GET | `/alerts` | List alerts |
| POST | `/alerts` | Create alert |
| PATCH | `/alerts/{id}` | Update alert |
| DELETE | `/alerts/{id}` | Delete alert |
| POST | `/alerts/{id}/test` | Send test Discord message |

### Create an alert (notify when ratio crosses **up** to 80)

```bash
curl -X POST http://127.0.0.1:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{"threshold": 80, "operator": "gte", "name": "Ratio at 80"}'
```

- `operator`: `gte` (>=) or `lte` (<=)
- If the ratio is **already** past the threshold when you create the alert, you will **not** get an immediate ping. The alert waits until the ratio moves back out of range and crosses again.

## Alert behavior

1. **Armed** — waiting for a cross into the satisfied zone.
2. **Fires once** when the condition becomes true (e.g. ratio goes from 79.5 to 80.1).
3. **Disarmed** while the condition stays true (no repeated Discord messages).
4. **Re-arms** when the condition becomes false (e.g. ratio drops below 80), so the next cross can notify again.

Poll interval defaults to **60 seconds** (`POLL_INTERVAL_SECONDS`).

## ApeWisdom trend detection

Optional pipeline that polls [ApeWisdom](https://apewisdom.io) stock mention rankings, stores historical snapshots (60 days), scores trends, sends Discord alerts, and posts a daily summary at **21:00 UTC**.

Enable in `.env`:

```bash
APEWISDOM_ENABLED=true
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ticker-trends` | Latest top tickers with trend scores (empty when disabled) |

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APEWISDOM_ENABLED` | `false` | Start trend fetch loop |
| `APEWISDOM_FETCH_INTERVAL_MINUTES` | `60` | Fetch interval |
| `APEWISDOM_MIN_MENTIONS` | `20` | Minimum mentions for ranking/API |
| `APEWISDOM_ALERT_MENTIONS` | `50` | Alert: mentions threshold |
| `APEWISDOM_ALERT_CHANGE_24H` | `100` | Alert: 24h % change threshold |
| `APEWISDOM_ALERT_SCORE_THRESHOLD` | `150` | Alert: trend score threshold (OR) |
| `APEWISDOM_ALERT_COOLDOWN_HOURS` | `6` | Per-ticker alert cooldown |
| `APEWISDOM_ALERT_MAX_PER_CYCLE` | `3` | Max tickers per Discord message (highest trend score) |
| `APEWISDOM_DAILY_SUMMARY_HOUR_UTC` | `21` | Daily Discord summary hour (UTC) |
| `APEWISDOM_HISTORY_DAYS` | `60` | Snapshot retention |
| `APEWISDOM_TOP_N` | `50` | Symbols stored per fetch |

### Trend score

`mentions * (1 + max(change_24h, 0) / 100)` — computed on read, not stored.

`change_24h` is `((mentions - mentions_24h_ago) / mentions_24h_ago) * 100` when `mentions_24h_ago > 0`, otherwise `null`.

### Alert rules

A symbol must have `mentions >= APEWISDOM_MIN_MENTIONS`, then triggers if **either**:

- `mentions >= APEWISDOM_ALERT_MENTIONS` **and** `change_24h >= APEWISDOM_ALERT_CHANGE_24H`
- `trend_score >= APEWISDOM_ALERT_SCORE_THRESHOLD`

Alerts use time-based cooldown (not ratio armed/disarmed). Each poll sends **one** Discord message with up to `APEWISDOM_ALERT_MAX_PER_CYCLE` tickers (default 3), ranked by trend score among symbols that pass cooldown.

### Tests

```bash
cd backend
uv sync --group dev
uv run pytest
```
