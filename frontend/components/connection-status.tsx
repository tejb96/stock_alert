import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type ConnectionStatusProps = {
  connected: boolean;
  isRefreshing?: boolean;
};

export function ConnectionStatus({
  connected,
  isRefreshing = false,
}: ConnectionStatusProps) {
  const label = isRefreshing
    ? "Refreshing"
    : connected
      ? "Connected"
      : "Disconnected";

  return (
    <Badge
      variant="outline"
      className={cn(
        "font-normal",
        isRefreshing && "border-amber-500/50 text-amber-600 dark:text-amber-400",
        !isRefreshing &&
          connected &&
          "border-emerald-500/50 text-emerald-600 dark:text-emerald-400",
        !isRefreshing &&
          !connected &&
          "border-destructive/50 text-destructive",
      )}
    >
      <span
        className={cn(
          "mr-1.5 inline-block size-1.5 rounded-full",
          isRefreshing && "bg-amber-500 animate-pulse",
          !isRefreshing && connected && "bg-emerald-500",
          !isRefreshing && !connected && "bg-destructive",
        )}
      />
      {label}
    </Badge>
  );
}
