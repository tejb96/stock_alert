"use client";

import { useState } from "react";
import { toast } from "sonner";

import { AlertsTable } from "@/components/alerts-table";
import { ConnectionStatus } from "@/components/connection-status";
import { CreateAlertDialog } from "@/components/create-alert-dialog";
import { RatioCard } from "@/components/ratio-card";
import { Separator } from "@/components/ui/separator";
import { useDashboardData } from "@/hooks/use-dashboard-data";
import {
  createAlert as apiCreateAlert,
  deleteAlert as apiDeleteAlert,
  messageFromError,
  testAlert as apiTestAlert,
  updateAlert as apiUpdateAlert,
} from "@/lib/api";
import type { AlertCreate } from "@/lib/types";

export function Dashboard() {
  const {
    status,
    health,
    ratio,
    alerts,
    error,
    isRefreshing,
    refresh,
    refreshAfterMutation,
  } = useDashboardData();

  const [createOpen, setCreateOpen] = useState(false);
  const [isMutating, setIsMutating] = useState(false);

  async function handleCreate(body: AlertCreate) {
    setIsMutating(true);
    try {
      await apiCreateAlert(body);
      await refreshAfterMutation();
      toast.success("Alert created");
      setCreateOpen(false);
    } catch (err) {
      toast.error(messageFromError(err));
      throw err;
    } finally {
      setIsMutating(false);
    }
  }

  async function handleToggleEnabled(id: number, enabled: boolean) {
    setIsMutating(true);
    try {
      await apiUpdateAlert(id, { enabled });
      await refreshAfterMutation();
      toast.success(enabled ? "Alert enabled" : "Alert paused");
    } catch (err) {
      toast.error(messageFromError(err));
    } finally {
      setIsMutating(false);
    }
  }

  async function handleTest(id: number) {
    setIsMutating(true);
    try {
      await apiTestAlert(id);
      toast.success("Test message sent to Discord");
    } catch (err) {
      toast.error(messageFromError(err));
    } finally {
      setIsMutating(false);
    }
  }

  async function handleDelete(id: number) {
    setIsMutating(true);
    try {
      await apiDeleteAlert(id);
      await refreshAfterMutation();
      toast.success("Alert deleted");
    } catch (err) {
      toast.error(messageFromError(err));
    } finally {
      setIsMutating(false);
    }
  }

  const busy = isRefreshing || isMutating;

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Gold / Silver Ratio Alerts
          </h1>
          <p className="text-sm text-muted-foreground">
            Watch the ratio and get Discord alerts on threshold crosses
          </p>
        </div>
        <ConnectionStatus
          connected={health?.ok ?? false}
          isRefreshing={busy}
        />
      </header>

      <RatioCard
        ratio={ratio}
        alerts={alerts}
        isLoading={status === "loading"}
        error={error}
        onRetry={refresh}
      />

      <Separator />

      <AlertsTable
        alerts={alerts}
        isLoading={status === "loading"}
        onToggleEnabled={handleToggleEnabled}
        onTest={handleTest}
        onDelete={handleDelete}
        onCreateClick={() => setCreateOpen(true)}
      />

      <CreateAlertDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSubmit={handleCreate}
        isSubmitting={isMutating}
      />
    </div>
  );
}
