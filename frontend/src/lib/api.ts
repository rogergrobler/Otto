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

export async function getProfile(): Promise<Profile> {
  return request<Profile>("/health/profile");
}

export async function updateProfile(
  data: Partial<Profile>
): Promise<Profile> {
  return request<Profile>("/health/profile", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ---- Labs ----

export interface LabResult {
  id: string;
  marker_name: string;
  value: number;
  unit: string;
  status: "optimal" | "normal" | "borderline" | "high" | "low" | "insufficient_data";
  reference_range?: string;
  tested_at: string;
}

export async function getLabs(): Promise<LabResult[]> {
  return request<LabResult[]>("/health/labs");
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
  return request<NutritionToday>("/health/nutrition/today");
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
  return request<NutritionEntry>("/health/nutrition", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ---- Goals ----

export interface Goal {
  id: string;
  domain: "cardiovascular" | "metabolic" | "neurological" | "cancer" | "general";
  title: string;
  description?: string;
  current_value?: number;
  target_value?: number;
  unit?: string;
  deadline?: string;
  status: "active" | "achieved" | "paused";
}

export async function getGoals(): Promise<Goal[]> {
  return request<Goal[]>("/health/goals");
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
  return request<WearableDay[]>("/health/wearables");
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

export async function getRisk(): Promise<RiskData> {
  return request<RiskData>("/health/risk");
}

// ---- Nudges ----

export interface Nudge {
  id: string;
  message: string;
  domain?: string;
  priority: "low" | "medium" | "high";
  acknowledged: boolean;
  created_at: string;
}

export async function getNudges(): Promise<Nudge[]> {
  return request<Nudge[]>("/nudges");
}

export async function acknowledgeNudge(id: string): Promise<void> {
  return request<void>(`/nudges/${id}/acknowledge`, { method: "POST" });
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
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message: text }),
  });
}
