"use client";

import { useState } from "react";
import { BellRing, Trash2 } from "lucide-react";

import { AlertStatusBadge } from "@/components/alert-status-badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCondition, formatRelativeTime } from "@/lib/format";
import type { Alert } from "@/lib/types";

export type AlertsTableProps = {
  alerts: Alert[];
  isLoading: boolean;
  onToggleEnabled: (id: number, enabled: boolean) => void;
  onTest: (id: number) => void;
  onDelete: (id: number) => void;
  onCreateClick: () => void;
};

export function AlertsTable({
  alerts,
  isLoading,
  onToggleEnabled,
  onTest,
  onDelete,
  onCreateClick,
}: AlertsTableProps) {
  const [deleteId, setDeleteId] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">Alerts</h2>
          <p className="text-sm text-muted-foreground">
            Discord notifications on threshold crosses
          </p>
        </div>
        <Button onClick={onCreateClick}>New alert</Button>
      </div>

      {isLoading && alerts.length === 0 ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : alerts.length === 0 ? (
        <div className="rounded-xl border border-dashed p-8 text-center">
          <p className="text-sm text-muted-foreground">
            No alerts yet. Create one to get notified when the ratio crosses
            your threshold.
          </p>
          <Button className="mt-4" variant="outline" onClick={onCreateClick}>
            New alert
          </Button>
        </div>
      ) : (
        <div className="rounded-xl ring-1 ring-foreground/10">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Condition</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last fired</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {alerts.map((alert) => (
                <TableRow key={alert.id}>
                  <TableCell className="font-medium">
                    {alert.name ?? `Alert #${alert.id}`}
                  </TableCell>
                  <TableCell>
                    {formatCondition(alert.operator, alert.threshold)}
                  </TableCell>
                  <TableCell>
                    <AlertStatusBadge
                      enabled={alert.enabled}
                      armed={alert.armed}
                    />
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {alert.last_fired_at
                      ? formatRelativeTime(alert.last_fired_at)
                      : "—"}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-2">
                      <Switch
                        checked={alert.enabled}
                        onCheckedChange={(enabled) =>
                          onToggleEnabled(alert.id, enabled)
                        }
                        aria-label={`Toggle alert ${alert.id}`}
                      />
                      <Button
                        variant="outline"
                        size="icon-sm"
                        onClick={() => onTest(alert.id)}
                        aria-label="Test Discord"
                      >
                        <BellRing className="size-4" />
                      </Button>
                      <Button
                        variant="destructive"
                        size="icon-sm"
                        onClick={() => setDeleteId(alert.id)}
                        aria-label="Delete alert"
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog
        open={deleteId !== null}
        onOpenChange={(open) => !open && setDeleteId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete alert?</DialogTitle>
            <DialogDescription>
              This cannot be undone. The alert will stop watching immediately.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (deleteId !== null) {
                  onDelete(deleteId);
                  setDeleteId(null);
                }
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
