"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  getTickerTrends,
  isAbortError,
  messageFromError,
} from "@/lib/api";
import type { TickerTrend, TrendsStatus } from "@/lib/types";

const DEFAULT_TRENDS_POLL_MS = 60_000;

function getTrendsPollIntervalMs(): number {
  const trendsRaw = process.env.NEXT_PUBLIC_TRENDS_POLL_INTERVAL_MS;
  if (trendsRaw) {
    const parsed = Number.parseInt(trendsRaw, 10);
    if (Number.isFinite(parsed) && parsed > 0) return parsed;
  }

  const fallbackRaw = process.env.NEXT_PUBLIC_POLL_INTERVAL_MS;
  if (fallbackRaw) {
    const parsed = Number.parseInt(fallbackRaw, 10);
    if (Number.isFinite(parsed) && parsed > 0) return parsed;
  }

  return DEFAULT_TRENDS_POLL_MS;
}

export type UseTickerTrendsReturn = {
  status: TrendsStatus;
  trends: TickerTrend[];
  error: string | null;
  lastUpdatedAt: Date | null;
  isRefreshing: boolean;
  refresh: () => Promise<void>;
};

export function useTickerTrends(): UseTickerTrendsReturn {
  const [status, setStatus] = useState<TrendsStatus>("loading");
  const [trends, setTrends] = useState<TickerTrend[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const isRefreshingRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  const runRefreshCycle = useCallback(async (): Promise<void> => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    isRefreshingRef.current = true;
    if (mountedRef.current) setIsRefreshing(true);

    try {
      const trendsResult = await getTickerTrends({ signal: controller.signal });

      if (controller.signal.aborted || !mountedRef.current) return;

      setTrends(trendsResult);
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
      }
    }
  }, []);

  const refresh = useCallback(async () => {
    if (isRefreshingRef.current) return;
    await runRefreshCycle();
  }, [runRefreshCycle]);

  useEffect(() => {
    mountedRef.current = true;
    const pollMs = getTrendsPollIntervalMs();

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
    trends,
    error,
    lastUpdatedAt,
    isRefreshing,
    refresh,
  };
}
