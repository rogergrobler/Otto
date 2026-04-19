const BASE_URL = "https://otto-production-924c.up.railway.app/api";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("otto_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.clear();
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(errBody || `HTTP ${res.status}`);
  }

  const text = await res.text();
  if (!text) return {} as T;
  return JSON.parse(text) as T;
}

// Multipart upload — does NOT set Content-Type (browser sets it with boundary)
async function upload<T>(path: string, formData: FormData): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.clear();
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(errBody || `HTTP ${res.status}`);
  }

  const text = await res.text();
  if (!text) return {} as T;
  return JSON.parse(text) as T;
}

// ---- Auth ----

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export interface RegisterData {
  full_name: string;
  email: string;
  password: string;
  weight_kg?: number;
  height_cm?: number;
}

export async function register(data: RegisterData): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function forgotPassword(email: string): Promise<{ reset_token: string }> {
  return request<{ reset_token: string }>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  await request("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

// ---- Profile ----

export interface Profile {
  id: string;
  full_name: string;
  email: string;
  weight_kg?: number;
  height_cm?: number;
  date_of_birth?: string;
  sex?: string;
  protein_target_g?: number;
  fibre_target_g?: number;
}

function adaptProfile(raw: Record<string, unknown>): Profile {
  return {
    ...(raw as unknown as Profile),
    protein_target_g:
      (raw.protein_target_g ?? raw.daily_protein_target_g) as number | undefined,
    fibre_target_g:
      (raw.fibre_target_g ?? raw.daily_fibre_target_g) as number | undefined,
  };
}

export async function getProfile(): Promise<Profile> {
  const raw = await request<Record<string, unknown>>("/health/profile");
  return adaptProfile(raw);
}

export async function updateProfile(
  data: Partial<Profile>
): Promise<Profile> {
  const payload: Record<string, unknown> = { ...data };
  if ("protein_target_g" in data) {
    payload.daily_protein_target_g = data.protein_target_g;
    delete payload.protein_target_g;
  }
  if ("fibre_target_g" in data) {
    payload.daily_fibre_target_g = data.fibre_target_g;
    delete payload.fibre_target_g;
  }
  const raw = await request<Record<string, unknown>>("/health/profile", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  return adaptProfile(raw);
}

// ---- Labs ----

export interface LabResult {
  id: string;
  marker_name: string;
  value: number | null;
  unit: string;
  status: "optimal" | "normal" | "borderline" | "high" | "low" | "insufficient_data";
  reference_range?: string;
  tested_at: string;
}

function mapFlag(flag: string | null | undefined): LabResult["status"] {
  const map: Record<string, LabResult["status"]> = {
    optimal: "optimal",
    normal: "normal",
    borderline: "borderline",
    high: "high",
    low: "low",
  };
  return map[flag ?? ""] ?? "normal";
}

function adaptLab(raw: Record<string, unknown>): LabResult {
  const low = raw.ref_range_low as number | null;
  const high = raw.ref_range_high as number | null;
  return {
    id: raw.id as string,
    marker_name: raw.marker_name as string,
    value: raw.value as number | null,
    unit: (raw.unit as string) ?? "",
    status: mapFlag(raw.flag as string | null),
    reference_range: low != null && high != null ? `${low}–${high}` : undefined,
    tested_at: (raw.test_date as string) ?? (raw.tested_at as string) ?? "",
  };
}

export async function getLabs(): Promise<LabResult[]> {
  const raw = await request<Record<string, unknown>[]>("/health/labs");
  return (raw ?? []).map(adaptLab);
}

export interface CreateLabData {
  marker_name: string;
  value: number;
  unit: string;
  tested_at: string;
  reference_range?: string;
}

export async function createLab(data: CreateLabData): Promise<LabResult> {
  const payload: Record<string, unknown> = {
    marker_name: data.marker_name,
    value: data.value,
    unit: data.unit,
    test_date: data.tested_at.slice(0, 10),
  };
  if (data.reference_range) {
    payload.notes = data.reference_range;
  }
  const raw = await request<Record<string, unknown>>("/health/labs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return adaptLab(raw);
}

export interface LabOCRMarker {
  marker_name: string;
  value: number | null;
  value_text?: string;
  unit?: string;
  flag?: string;
  ref_range_low?: number;
  ref_range_high?: number;
  test_date?: string;
  lab_name?: string;
  notes?: string;
}

export interface LabOCRResult {
  lab_name?: string;
  test_date?: string;
  markers: LabOCRMarker[];
}

export async function uploadLabPDF(file: File): Promise<LabOCRResult> {
  const form = new FormData();
  form.append("file", file);
  return upload<LabOCRResult>("/health/labs/upload", form);
}

export async function confirmLabOCR(payload: LabOCRResult): Promise<LabResult[]> {
  const raw = await request<Record<string, unknown>[]>("/health/labs/confirm", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return (raw ?? []).map(adaptLab);
}

// ---- Nutrition ----

export interface NutritionEntry {
  id: string;
  meal_name: string;
  calories?: number;
  protein_g?: number;
  fibre_g?: number;
  carbs_g?: number;
  fat_g?: number;
  logged_at: string;
}

export interface NutritionToday {
  entries: NutritionEntry[];
  totals: {
    calories: number;
    protein_g: number;
    fibre_g: number;
    carbs_g: number;
    fat_g: number;
  };
  targets: {
    protein_g: number;
    fibre_g: number;
  };
}

export async function getNutritionToday(): Promise<NutritionToday> {
  const raw = await request<Record<string, unknown>>("/health/nutrition/today");
  const meals = (raw.meals as Record<string, unknown>[] | undefined) ?? [];
  const targets = (raw.targets as Record<string, number | null> | undefined) ?? {};
  return {
    entries: meals.map((m) => ({
      id: m.id as string,
      meal_name: (m.description as string) || (m.meal_type as string) || "Meal",
      calories: (m.calories as number | undefined) ?? undefined,
      protein_g: (m.protein_g as number | undefined) ?? undefined,
      fibre_g: (m.fibre_g as number | undefined) ?? undefined,
      carbs_g: (m.carbs_net_g as number | undefined) ?? undefined,
      fat_g: (m.fat_g as number | undefined) ?? undefined,
      logged_at: (m.created_at as string) ?? (raw.date as string) ?? new Date().toISOString(),
    })),
    totals: {
      calories: (raw.total_calories as number) ?? 0,
      protein_g: (raw.total_protein_g as number) ?? 0,
      fibre_g: (raw.total_fibre_g as number) ?? 0,
      carbs_g: (raw.total_carbs_net_g as number) ?? 0,
      fat_g: (raw.total_fat_g as number) ?? 0,
    },
    targets: {
      protein_g: (targets.protein_g as number | null) ?? 0,
      fibre_g: (targets.fibre_g as number | null) ?? 0,
    },
  };
}

export interface LogMealData {
  meal_name: string;
  calories?: number;
  protein_g?: number;
  fibre_g?: number;
  carbs_g?: number;
  fat_g?: number;
}

export async function logMeal(data: LogMealData): Promise<NutritionEntry> {
  const payload = {
    log_date: new Date().toISOString().slice(0, 10),
    description: data.meal_name,
    meal_type: "other",
    calories: data.calories,
    protein_g: data.protein_g,
    fibre_g: data.fibre_g,
    carbs_net_g: data.carbs_g,
    fat_g: data.fat_g,
  };
  const raw = await request<Record<string, unknown>>("/health/nutrition", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return {
    id: raw.id as string,
    meal_name: (raw.description as string) || "Meal",
    calories: raw.calories as number | undefined,
    protein_g: raw.protein_g as number | undefined,
    fibre_g: raw.fibre_g as number | undefined,
    carbs_g: raw.carbs_net_g as number | undefined,
    fat_g: raw.fat_g as number | undefined,
    logged_at: (raw.created_at as string) ?? new Date().toISOString(),
  };
}

export interface MealAnalysis {
  description: string;
  meal_type: string;
  calories?: number;
  protein_g?: number;
  fat_g?: number;
  carbs_net_g?: number;
  fibre_g?: number;
  omega3_g?: number;
  confidence: "high" | "medium" | "low";
  notes?: string;
}

export async function analyseMealPhoto(file: File): Promise<MealAnalysis> {
  const form = new FormData();
  form.append("file", file);
  return upload<MealAnalysis>("/health/nutrition/analyse", form);
}

export async function confirmMealAnalysis(
  analysis: MealAnalysis
): Promise<NutritionEntry> {
  const raw = await request<Record<string, unknown>>("/health/nutrition/confirm", {
    method: "POST",
    body: JSON.stringify(analysis),
  });
  return {
    id: raw.id as string,
    meal_name: (raw.description as string) || "Meal",
    calories: raw.calories as number | undefined,
    protein_g: raw.protein_g as number | undefined,
    fibre_g: raw.fibre_g as number | undefined,
    carbs_g: raw.carbs_net_g as number | undefined,
    fat_g: raw.fat_g as number | undefined,
    logged_at: (raw.created_at as string) ?? new Date().toISOString(),
  };
}

// ---- Goals ----

export interface Goal {
  id: string;
  domain: "cardiovascular" | "metabolic" | "neurological" | "cancer" | "cancer_prevention" | "nutrition" | "training" | "body_composition" | "sleep" | "supplements" | "general";
  title: string;
  description?: string;
  current_value?: number;
  target_value?: number;
  unit?: string;
  deadline?: string;
  status: "active" | "achieved" | "paused";
}

function parseGoalNumeric(v: unknown): number | undefined {
  if (v == null || v === "") return undefined;
  const n = parseFloat(v as string);
  return Number.isFinite(n) ? n : undefined;
}

export async function getGoals(): Promise<Goal[]> {
  const raw = await request<Record<string, unknown>[]>("/health/goals");
  return (raw ?? []).map((g) => {
    const rawStatus = g.status as string;
    const status: Goal["status"] =
      rawStatus === "completed" ? "achieved" :
      rawStatus === "abandoned" ? "paused" :
      rawStatus === "paused" ? "paused" : "active";
    return {
      id: g.id as string,
      domain: (g.domain as Goal["domain"]) ?? "general",
      title: (g.goal_text as string) ?? (g.title as string) ?? "",
      description: g.target_metric as string | undefined,
      current_value: parseGoalNumeric(g.current_value),
      target_value: parseGoalNumeric(g.target_value),
      deadline: g.deadline as string | undefined,
      status,
    };
  });
}

export interface CreateGoalData {
  domain: Goal["domain"];
  goal_text: string;
  target_metric?: string;
  deadline?: string;
}

export async function createGoal(data: CreateGoalData): Promise<Goal> {
  const raw = await request<Record<string, unknown>>("/health/goals", {
    method: "POST",
    body: JSON.stringify(data),
  });
  return {
    id: raw.id as string,
    domain: (raw.domain as Goal["domain"]) ?? "general",
    title: (raw.goal_text as string) ?? "",
    description: raw.target_metric as string | undefined,
    current_value: undefined,
    target_value: undefined,
    deadline: raw.deadline as string | undefined,
    status: "active",
  };
}

// ---- Wearables ----

export interface WearableDay {
  date: string;
  sleep_hours?: number;
  hrv_ms?: number;
  recovery_score?: number;
  zone2_mins?: number;
  steps?: number;
}

export async function getWearables(): Promise<WearableDay[]> {
  const raw = await request<Record<string, unknown>[]>("/health/wearables");
  return (raw ?? []).map((w) => ({
    date: (w.data_date as string) ?? (w.date as string) ?? "",
    sleep_hours: w.sleep_hours as number | undefined,
    hrv_ms: w.hrv_ms as number | undefined,
    recovery_score: w.recovery_score as number | undefined,
    zone2_mins: (w.zone2_minutes as number | undefined) ?? (w.zone2_mins as number | undefined),
    steps: w.steps as number | undefined,
  }));
}

export async function upsertWearable(data: Partial<WearableDay> & { date: string }): Promise<WearableDay> {
  const payload = {
    data_date: data.date,
    source: "manual",
    sleep_hours: data.sleep_hours,
    hrv_ms: data.hrv_ms,
    recovery_score: data.recovery_score,
    zone2_minutes: data.zone2_mins,
    steps: data.steps,
  };
  const raw = await request<Record<string, unknown>>("/health/wearables", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return {
    date: raw.data_date as string,
    sleep_hours: raw.sleep_hours as number | undefined,
    hrv_ms: raw.hrv_ms as number | undefined,
    recovery_score: raw.recovery_score as number | undefined,
    zone2_mins: raw.zone2_minutes as number | undefined,
    steps: raw.steps as number | undefined,
  };
}

// ---- WHOOP ----

export interface WhoopStatus {
  connected: boolean;
  provider_user_id?: string;
  token_expiry?: string;
}

export async function getWhoopStatus(): Promise<WhoopStatus> {
  return request<WhoopStatus>("/integrations/whoop/status");
}

export async function getWhoopConnectUrl(): Promise<{ url: string }> {
  return request<{ url: string }>("/integrations/whoop/connect-url");
}

export async function syncWhoop(): Promise<{ status: string; synced: Record<string, number>; message: string }> {
  return request("/integrations/whoop/sync", { method: "POST" });
}

// ---- Risk ----

export interface RiskData {
  overall_score: number;
  domains: {
    cardiovascular: "green" | "amber" | "red" | "insufficient_data";
    metabolic: "green" | "amber" | "red" | "insufficient_data";
    neurological: "green" | "amber" | "red" | "insufficient_data";
    cancer: "green" | "amber" | "red" | "insufficient_data";
  };
}

type RagStatus = "green" | "amber" | "red" | "insufficient_data";

export async function getRisk(): Promise<RiskData> {
  const raw = await request<Record<string, unknown>>("/health/risk");
  const domainMap: Record<string, RagStatus> = {};
  const domains = (raw.domains as Record<string, unknown>[]) ?? [];
  domains.forEach((d) => {
    domainMap[d.domain as string] = (d.rag_status as RagStatus) ?? "insufficient_data";
  });
  return {
    overall_score: (raw.health_score as number) ?? 0,
    domains: {
      cardiovascular: domainMap.cardiovascular ?? "insufficient_data",
      metabolic: domainMap.metabolic ?? "insufficient_data",
      neurological: domainMap.neurological ?? "insufficient_data",
      cancer: domainMap.cancer_prevention ?? domainMap.cancer ?? "insufficient_data",
    },
  };
}

// ---- Nudges ----

export interface Nudge {
  id: string;
  nudge_type: string;
  message: string;
  scheduled_at: string;
  sent_at: string | null;
  acknowledged_at: string | null;
}

export async function getNudges(unreadOnly = false): Promise<Nudge[]> {
  return request<Nudge[]>(`/nudges?unread_only=${unreadOnly}`);
}

export async function acknowledgeNudge(id: string): Promise<Nudge> {
  return request<Nudge>(`/nudges/${id}/acknowledge`, { method: "POST" });
}

// ---- Chat ----

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

export interface ChatResponse {
  reply: string;
  message?: ChatMessage;
}

export async function sendMessage(text: string): Promise<ChatResponse> {
  const raw = await request<Record<string, unknown>>("/chat", {
    method: "POST",
    body: JSON.stringify({ message: text }),
  });
  return {
    reply: (raw.response as string) ?? (raw.reply as string) ?? "",
    message: raw.message as ChatMessage | undefined,
  };
}
