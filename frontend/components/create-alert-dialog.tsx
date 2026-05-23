"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import type { AlertCreate } from "@/lib/types";

const schema = z.object({
  name: z.string().optional(),
  threshold: z.number().positive("Threshold must be greater than 0"),
  operator: z.enum(["gte", "lte"]),
  enabled: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

export type CreateAlertDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (body: AlertCreate) => Promise<void>;
  isSubmitting: boolean;
};

export function CreateAlertDialog({
  open,
  onOpenChange,
  onSubmit,
  isSubmitting,
}: CreateAlertDialogProps) {
  const form = useForm<FormValues>({
    defaultValues: {
      name: "",
      threshold: 80,
      operator: "gte",
      enabled: true,
    },
  });

  async function handleSubmit(raw: FormValues) {
    const result = schema.safeParse(raw);
    if (!result.success) {
      for (const issue of result.error.issues) {
        const field = issue.path[0];
        if (
          field === "name" ||
          field === "threshold" ||
          field === "operator" ||
          field === "enabled"
        ) {
          form.setError(field, { message: issue.message });
        }
      }
      return;
    }

    const values = result.data;
    await onSubmit({
      name: values.name?.trim() || null,
      threshold: values.threshold,
      operator: values.operator,
      enabled: values.enabled,
    });
    form.reset();
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New alert</DialogTitle>
          <DialogDescription>
            You will get one Discord message per cross, not while the ratio stays
            past the threshold.
          </DialogDescription>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={form.handleSubmit(handleSubmit)}
        >
          <div className="space-y-2">
            <Label htmlFor="name">Name (optional)</Label>
            <Input
              id="name"
              placeholder="Ratio at 80"
              {...form.register("name")}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="threshold">Threshold</Label>
            <Input
              id="threshold"
              type="number"
              step="0.01"
              {...form.register("threshold", { valueAsNumber: true })}
            />
            {form.formState.errors.threshold ? (
              <p className="text-sm text-destructive">
                {form.formState.errors.threshold.message}
              </p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label>Condition</Label>
            <Select
              value={form.watch("operator")}
              onValueChange={(v) =>
                form.setValue("operator", v as "gte" | "lte")
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gte">At or above</SelectItem>
                <SelectItem value="lte">At or below</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center justify-between">
            <Label htmlFor="enabled">Enabled</Label>
            <Switch
              id="enabled"
              checked={form.watch("enabled")}
              onCheckedChange={(v) => form.setValue("enabled", v)}
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating…" : "Create alert"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
