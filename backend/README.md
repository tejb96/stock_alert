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
