"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getHealth, getRatio, isAbortError, listAlerts, messageFromError } from "@/lib/api";
import type { Alert, DashboardStatus, Health, Ratio } from "@/lib/types";

const DEFAULT_POLL_MS = 30_000;

function getPollIntervalMs(): number {
  const raw = process.env.NEXT_PUBLIC_POLL_INTERVAL_MS;
  if (!raw) return DEFAULT_POLL_MS;
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_POLL_MS;
}

export type UseDashboardDataReturn = {
  status: DashboardStatus;
  health: Health | null;
  ratio: Ratio | null;
  alerts: Alert[];
  error: string | null;
  lastUpdatedAt: Date | null;
  isRefreshing: boolean;
  refresh: () => Promise<void>;
  refreshAfterMutation: () => Promise<void>;
};

export function useDashboardData(): UseDashboardDataReturn {
  const [status, setStatus] = useState<DashboardStatus>("loading");
  const [health, setHealth] = useState<Health | null>(null);
  const [ratio, setRatio] = useState<Ratio | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const isRefreshingRef = useRef(false);
  const inFlightRef = useRef<Promise<void> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  const runRefreshCycle = useCallback(async (): Promise<void> => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    isRefreshingRef.current = true;
    if (mountedRef.current) setIsRefreshing(true);

    try {
      const [healthResult, ratioResult, alertsResult] = await Promise.all([
        getHealth({ signal: controller.signal }),
        getRatio({ signal: controller.signal }),
        listAlerts({ signal: controller.signal }),
      ]);

      if (controller.signal.aborted || !mountedRef.current) return;

      setHealth(healthResult);
      setRatio(ratioResult);
      setAlerts(alertsResult);
      setStatus("ready");
      setError(null);
      setLastUpdatedAt(new Date());
    } catch (err) {
      if (isAbortError(err) || controller.signal.aborted || !mountedRef.current) {
        return;
      }
      setStatus("error");
      setError(messageFromError(err));
    } finally {
      if (abortRef.current === controller) {
        isRefreshingRef.current = false;
        if (mountedRef.current) setIsRefreshing(false);
        inFlightRef.current = null;
      }
    }
  }, []);

  const refresh = useCallback(async () => {
    if (isRefreshingRef.current) return;
    inFlightRef.current = runRefreshCycle();
    await inFlightRef.current;
  }, [runRefreshCycle]);

  const refreshAfterMutation = useCallback(async () => {
    if (inFlightRef.current) {
      await inFlightRef.current.catch(() => {});
    }
    inFlightRef.current = runRefreshCycle();
    await inFlightRef.current;
  }, [runRefreshCycle]);

  useEffect(() => {
    mountedRef.current = true;
    const pollMs = getPollIntervalMs();

    void refresh();

    const intervalId = setInterval(() => {
      void refresh();
    }, pollMs);

    return () => {
      mountedRef.current = false;
      clearInterval(intervalId);
      abortRef.current?.abort();
    };
  }, [refresh]);

  return {
    status,
    health,
    ratio,
    alerts,
    error,
    lastUpdatedAt,
    isRefreshing,
    refresh,
    refreshAfterMutation,
  };
}
