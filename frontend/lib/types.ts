export type AlertOperator = "gte" | "lte";

export type Alert = {
  id: number;
  name: string | null;
  threshold: number;
  operator: AlertOperator;
  enabled: boolean;
  armed: boolean;
  created_at: string;
  last_fired_at: string | null;
};

export type AlertCreate = {
  threshold: number;
  operator?: AlertOperator;
  name?: string | null;
  enabled?: boolean;
};

export type AlertUpdate = {
  threshold?: number;
  operator?: AlertOperator;
  name?: string | null;
  enabled?: boolean;
};

export type Ratio = {
  ratio: number;
  gold_price: number;
  silver_price: number;
  source: string;
  fetched_at: string;
  market_state: string;
};

export type Health = {
  ok: boolean;
};

export type DashboardStatus = "loading" | "ready" | "error";
