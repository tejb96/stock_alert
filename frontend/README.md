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
useDashboardData (single poll + server state)
        ↓
dashboard.tsx (mutations + wiring)
        ↓
presentational components (props only)
```

### Rules

| Layer | Responsibility |
|-------|----------------|
| `hooks/use-dashboard-data.ts` | One `setInterval`, read fetches (`health`, `ratio`, `alerts`), `refresh` / `refreshAfterMutation` |
| `components/dashboard.tsx` | Mutations via `lib/api.ts`, toasts, passes props |
| Presentational components | No `fetch`, no hook imports |

### Concurrency

- **`refresh()`** — skips if a cycle is already in progress (interval ticks do not stack).
- **`refreshAfterMutation()`** — waits for in-flight refresh, then runs one new cycle.
- **AbortController** — aborts the previous cycle before starting a new one; ignores stale responses.

### Imports

- Hook → read APIs only: `getHealth`, `getRatio`, `listAlerts`
- Dashboard → mutation APIs: `createAlert`, `updateAlert`, `deleteAlert`, `testAlert`
- No React Context for server state in v1

## Dev (two terminals)

```bash
# Terminal 1 — API
cd backend && uv run fastapi dev app.main:app

# Terminal 2 — UI
cd frontend && pnpm dev
```

Open http://localhost:3000
