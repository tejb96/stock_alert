import { AlertCircle, RefreshCw } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  distanceToThreshold,
  formatPrice,
  formatRatio,
  formatRelativeTime,
} from "@/lib/format";
import type { Alert as AlertType, Ratio } from "@/lib/types";

export type RatioCardProps = {
  ratio: Ratio | null;
  alerts: AlertType[];
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
};

export function RatioCard({
  ratio,
  alerts,
  isLoading,
  error,
  onRetry,
}: RatioCardProps) {
  const hint = ratio ? distanceToThreshold(ratio, alerts) : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Gold / Silver ratio</CardTitle>
        <CardDescription>
          Live COMEX futures proxy (GC=F / SI=F)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && !ratio ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-32" />
            <Skeleton className="h-4 w-full max-w-sm" />
            <Skeleton className="h-4 w-48" />
          </div>
        ) : error && !ratio ? (
          <Alert variant="destructive">
            <AlertCircle className="size-4" />
            <AlertTitle>Could not load ratio</AlertTitle>
            <AlertDescription className="flex flex-col gap-3">
              <span>{error}</span>
              <Button variant="outline" size="sm" className="w-fit" onClick={onRetry}>
                <RefreshCw className="size-4" />
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        ) : ratio ? (
          <>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-semibold tracking-tight tabular-nums">
                {formatRatio(ratio.ratio)}
              </span>
            </div>
            <div className="grid gap-1 text-sm text-muted-foreground sm:grid-cols-2">
              <p>Gold: {formatPrice(ratio.gold_price)}/oz</p>
              <p>Silver: {formatPrice(ratio.silver_price)}/oz</p>
              <p>Market: {ratio.market_state}</p>
              <p>Updated: {formatRelativeTime(ratio.fetched_at)}</p>
            </div>
            {hint ? (
              <p className="text-sm text-muted-foreground">{hint}</p>
            ) : null}
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}
