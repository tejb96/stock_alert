import { Badge } from "@/components/ui/badge";

export type AlertStatusBadgeProps = {
  enabled: boolean;
  armed: boolean;
};

export function AlertStatusBadge({ enabled, armed }: AlertStatusBadgeProps) {
  if (!enabled) {
    return <Badge variant="secondary">Paused</Badge>;
  }
  if (armed) {
    return <Badge variant="outline">Watching</Badge>;
  }
  return <Badge>In range</Badge>;
}
