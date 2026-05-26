# Gold / Silver Ratio Alerts — Frontend

Next.js dashboard for the [FastAPI backend](../backend/README.md).

## Setup

```bash
cd frontend
cp .env.local.example .env.local
pnpm install
pnpm dev
```

Backend must be running at `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`).

## Architecture

```
useDashboardData ──┐
                   ├──► dashboard.tsx (mutations + wiring)
useTickerTrends ───┘           ↓
                    presentational components (props only)
```

### Rules

| Layer | Responsibility |
|-------|----------------|
| `hooks/use-dashboard-data.ts` | Poll `health`, `ratio`, `alerts`; `refresh` / `refreshAfterMutation` |
| `hooks/use-ticker-trends.ts` | Poll `GET /ticker-trends` on its own interval; errors isolated from ratio/alerts |
| `components/dashboard.tsx` | Mutations via `lib/api.ts`, toasts, passes props |
| Presentational components | No `fetch`, no hook imports |

### Concurrency

- **`refresh()`** — skips if a cycle is already in progress (interval ticks do not stack).
- **`refreshAfterMutation()`** — waits for in-flight refresh, then runs one new cycle.
- **AbortController** — aborts the previous cycle before starting a new one; ignores stale responses.

### Imports

- `useDashboardData` → `getHealth`, `getRatio`, `listAlerts`
- `useTickerTrends` → `getTickerTrends`
- Dashboard → mutation APIs: `createAlert`, `updateAlert`, `deleteAlert`, `testAlert`
- No React Context for server state in v1

### Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Backend base URL |
| `NEXT_PUBLIC_POLL_INTERVAL_MS` | `30000` | Ratio + alerts poll interval |
| `NEXT_PUBLIC_TRENDS_POLL_INTERVAL_MS` | `60000` | Ticker trends poll interval |

Backend must have `APEWISDOM_ENABLED=true` for trend rows; see [backend README](../backend/README.md#apewisdom-trend-detection).

### Manual QA (trends)

1. `APEWISDOM_ENABLED=false` → empty trends message; ratio and alerts still load.
2. Enable backend trends → table fills after first fetch; column sort works.
3. Break `/ticker-trends` → trends section shows error; ratio section unaffected.
4. Trends Retry refetches trends only.

## Dev (two terminals)

```bash
# Terminal 1 — API
cd backend && uv run fastapi dev app.main:app

# Terminal 2 — UI
cd frontend && pnpm dev
```

Open http://localhost:3000
