"use client";

import { useMemo, useState } from "react";
import { AlertCircle, ArrowDown, ArrowUp, ArrowUpDown, RefreshCw } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  formatMentions,
  formatPercentChange,
  formatRelativeTime,
  formatTrendScore,
  formatUpvotes,
  trendChangeVariant,
} from "@/lib/format";
import type { TickerTrend, TrendSortKey } from "@/lib/types";
import { cn } from "@/lib/utils";

export type TickerTrendsTableProps = {
  trends: TickerTrend[];
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  lastUpdatedAt?: Date | null;
};

type SortDirection = "asc" | "desc";

function sortValue(row: TickerTrend, key: TrendSortKey): number {
  switch (key) {
    case "rank":
      return row.rank;
    case "mentions":
      return row.mentions;
    case "upvotes":
      return row.upvotes;
    case "trend_score":
      return row.trend_score;
    case "change_24h":
      return row.change_24h ?? Number.NEGATIVE_INFINITY;
  }
}

function sortedTrends(
  trends: TickerTrend[],
  key: TrendSortKey,
  direction: SortDirection,
): TickerTrend[] {
  const copy = [...trends];
  copy.sort((a, b) => {
    const av = sortValue(a, key);
    const bv = sortValue(b, key);
    if (av === bv) return a.rank - b.rank;
    return direction === "asc" ? av - bv : bv - av;
  });
  return copy;
}

function SortIcon({
  active,
  direction,
}: {
  active: boolean;
  direction: SortDirection;
}) {
  if (!active) return <ArrowUpDown className="size-3.5 opacity-50" />;
  return direction === "asc" ? (
    <ArrowUp className="size-3.5" />
  ) : (
    <ArrowDown className="size-3.5" />
  );
}

export function TickerTrendsTable({
  trends,
  isLoading,
  error,
  onRetry,
  lastUpdatedAt,
}: TickerTrendsTableProps) {
  const [sortKey, setSortKey] = useState<TrendSortKey>("rank");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const displayTrends = useMemo(
    () => sortedTrends(trends, sortKey, sortDirection),
    [trends, sortKey, sortDirection],
  );

  function toggleSort(key: TrendSortKey) {
    if (sortKey === key) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection(key === "rank" ? "asc" : "desc");
    }
  }

  function sortableHead(label: string, key: TrendSortKey, className?: string) {
    const active = sortKey === key;
    return (
      <TableHead className={className}>
        <button
          type="button"
          onClick={() => toggleSort(key)}
          className="inline-flex items-center gap-1 font-medium hover:text-foreground"
        >
          {label}
          <SortIcon active={active} direction={sortDirection} />
        </button>
      </TableHead>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-medium">ApeWisdom trends</h2>
        <p className="text-sm text-muted-foreground">
          Stock mention rankings from Reddit; refreshed on the server fetch interval
        </p>
      </div>

      {isLoading && trends.length === 0 ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : error && trends.length === 0 ? (
        <Alert variant="destructive">
          <AlertCircle className="size-4" />
          <AlertTitle>Could not load trends</AlertTitle>
          <AlertDescription className="flex flex-col gap-3">
            <span>{error}</span>
            <Button variant="outline" size="sm" className="w-fit" onClick={onRetry}>
              <RefreshCw className="size-4" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      ) : trends.length === 0 ? (
        <div className="rounded-xl border border-dashed p-8 text-center">
          <p className="text-sm text-muted-foreground">
            No trend data yet. Enable{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">
              APEWISDOM_ENABLED
            </code>{" "}
            on the backend and wait for the next fetch cycle.
          </p>
        </div>
      ) : (
        <>
          <div className="rounded-xl ring-1 ring-foreground/10">
            <Table>
              <TableHeader>
                <TableRow>
                  {sortableHead("Rank", "rank", "w-16")}
                  <TableHead>Ticker</TableHead>
                  {sortableHead("Mentions", "mentions", "text-right")}
                  {sortableHead("24h change", "change_24h", "text-right")}
                  {sortableHead("Upvotes", "upvotes", "text-right")}
                  {sortableHead("Trend score", "trend_score", "text-right")}
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayTrends.map((row) => {
                  const variant = trendChangeVariant(row.change_24h);
                  return (
                    <TableRow key={row.ticker}>
                      <TableCell className="tabular-nums text-muted-foreground">
                        {row.rank}
                      </TableCell>
                      <TableCell className="font-medium">{row.ticker}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatMentions(row.mentions)}
                      </TableCell>
                      <TableCell className="text-right">
                        {row.change_24h !== null && row.change_24h >= 100 ? (
                          <Badge
                            variant="secondary"
                            className={cn(
                              "tabular-nums",
                              variant === "positive" &&
                                "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400",
                              variant === "negative" &&
                                "bg-red-500/15 text-red-700 dark:text-red-400",
                            )}
                          >
                            {formatPercentChange(row.change_24h)}
                          </Badge>
                        ) : (
                          <span
                            className={cn(
                              "tabular-nums",
                              variant === "positive" &&
                                "text-emerald-600 dark:text-emerald-400",
                              variant === "negative" &&
                                "text-red-600 dark:text-red-400",
                              variant === "muted" && "text-muted-foreground",
                            )}
                          >
                            {formatPercentChange(row.change_24h)}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {formatUpvotes(row.upvotes)}
                      </TableCell>
                      <TableCell className="text-right font-medium tabular-nums">
                        {formatTrendScore(row.trend_score)}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
          {lastUpdatedAt ? (
            <p className="text-xs text-muted-foreground">
              Updated {formatRelativeTime(lastUpdatedAt.toISOString())}
            </p>
          ) : null}
        </>
      )}
    </div>
  );
}
