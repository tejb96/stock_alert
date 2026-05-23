import type { Alert, AlertOperator, Ratio } from "@/lib/types";

export function formatRatio(value: number): string {
  return value.toFixed(2);
}

export function formatPrice(value: number): string {
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

export function formatCondition(
  operator: AlertOperator,
  threshold: number,
): string {
  const symbol = operator === "gte" ? "≥" : "≤";
  return `${symbol} ${formatRatio(threshold)}`;
}

export function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return date.toLocaleString();
}

export function distanceToThreshold(
  ratio: Ratio,
  alerts: Alert[],
): string | null {
  const active = alerts.filter((a) => a.enabled);
  if (active.length === 0) return null;

  let best: { delta: number; text: string } | null = null;

  for (const alert of active) {
    const delta =
      alert.operator === "gte"
        ? alert.threshold - ratio.ratio
        : ratio.ratio - alert.threshold;

    const text =
      delta > 0
        ? `${formatRatio(delta)} below ${formatCondition(alert.operator, alert.threshold)}`
        : delta < 0
          ? `${formatRatio(Math.abs(delta))} above ${formatCondition(alert.operator, alert.threshold)}`
          : `at ${formatCondition(alert.operator, alert.threshold)}`;

    if (!best || Math.abs(delta) < Math.abs(best.delta)) {
      best = { delta, text };
    }
  }

  return best?.text ?? null;
}
