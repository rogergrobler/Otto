"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { getNutritionToday, logMeal, analyseMealPhoto, confirmMealAnalysis } from "@/lib/api";
import type { NutritionToday, LogMealData, MealAnalysis } from "@/lib/api";

function MacroBar({
  label,
  value,
  target,
  unit,
  color,
}: {
  label: string;
  value: number;
  target: number;
  unit: string;
  color: string;
}) {
  const pct = target > 0 ? Math.min(100, (value / target) * 100) : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span className="text-gray-300 font-medium">{label}</span>
        <span className="text-gray-400">
          <span className="text-white font-medium">{value.toFixed(0)}</span>
          <span className="text-gray-600"> / {target}{unit}</span>
        </span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-gray-600">{pct.toFixed(0)}% of daily target</p>
    </div>
  );
}

function LogMealModal({
  onClose,
  onLogged,
}: {
  onClose: () => void;
  onLogged: () => void;
}) {
  const [tab, setTab] = useState<"photo" | "manual">("photo");
  const [form, setForm] = useState<LogMealData>({ meal_name: "", calories: undefined, protein_g: undefined, fibre_g: undefined, carbs_g: undefined, fat_g: undefined });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Photo flow state
  const [analysis, setAnalysis] = useState<MealAnalysis | null>(null);
  const [analysing, setAnalysing] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value === "" ? undefined : name === "meal_name" ? value : parseFloat(value) }));
  }

  async function handleManualSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.meal_name.trim()) return;
    setError(null);
    setLoading(true);
    try {
      await logMeal(form);
      onLogged();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to log meal.");
    } finally {
      setLoading(false);
    }
  }

  async function handlePhotoFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setAnalysing(true);
    try {
      const result = await analyseMealPhoto(file);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyse photo.");
    } finally {
      setAnalysing(false);
    }
  }

  async function handleConfirmPhoto() {
    if (!analysis) return;
    setLoading(true);
    setError(null);
    try {
      await confirmMealAnalysis(analysis);
      onLogged();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save meal.");
    } finally {
      setLoading(false);
    }
  }

  const confidenceColor = analysis?.confidence === "high" ? "text-green-400" : analysis?.confidence === "medium" ? "text-amber-400" : "text-red-400";

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60">
      <div className="w-full max-w-md bg-[#111111] rounded-t-3xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Log a Meal</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M5.47 5.47a.75.75 0 0 1 1.06 0L12 10.94l5.47-5.47a.75.75 0 1 1 1.06 1.06L13.06 12l5.47 5.47a.75.75 0 1 1-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 0 1-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 bg-[#1a1a1a] rounded-xl p-1">
          {(["photo", "manual"] as const).map((t) => (
            <button key={t} onClick={() => { setTab(t); setAnalysis(null); setError(null); }}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${tab === t ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-300"}`}>
              {t === "photo" ? "📷 Photo" : "Manual"}
            </button>
          ))}
        </div>

        {error && <p className="text-red-400 text-sm bg-red-500/10 px-3 py-2 rounded-lg">{error}</p>}

        {/* Photo tab */}
        {tab === "photo" && (
          <div className="space-y-3">
            {!analysis && !analysing && (
              <>
                <button onClick={() => fileRef.current?.click()}
                  className="w-full h-32 border-2 border-dashed border-gray-700 rounded-2xl flex flex-col items-center justify-center gap-2 hover:border-blue-500 hover:bg-blue-500/5 transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-gray-600">
                    <path fillRule="evenodd" d="M1.5 6a2.25 2.25 0 0 1 2.25-2.25h16.5A2.25 2.25 0 0 1 22.5 6v12a2.25 2.25 0 0 1-2.25 2.25H3.75A2.25 2.25 0 0 1 1.5 18V6ZM3 16.06V18c0 .414.336.75.75.75h16.5A.75.75 0 0 0 21 18v-1.94l-2.69-2.689a1.5 1.5 0 0 0-2.12 0l-.88.879.97.97a.75.75 0 1 1-1.06 1.06l-5.16-5.159a1.5 1.5 0 0 0-2.12 0L3 16.061Zm10.125-7.81a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm text-gray-400">Take or upload a photo</p>
                </button>
                <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={handlePhotoFile} />
                <p className="text-xs text-gray-600 text-center">Claude Vision estimates the macros. You confirm before saving.</p>
              </>
            )}

            {analysing && (
              <div className="flex flex-col items-center py-8 gap-3">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-gray-400 text-sm">Analysing your meal…</p>
              </div>
            )}

            {analysis && (
              <div className="space-y-3">
                <div className="bg-[#1a1a1a] rounded-xl p-4 space-y-2">
                  <div className="flex items-start justify-between">
                    <p className="text-sm font-medium text-white">{analysis.description}</p>
                    <span className={`text-xs font-medium ${confidenceColor}`}>{analysis.confidence} confidence</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 pt-1">
                    {[
                      { label: "Protein", value: analysis.protein_g, unit: "g", color: "text-blue-400" },
                      { label: "Fibre", value: analysis.fibre_g, unit: "g", color: "text-green-400" },
                      { label: "Carbs", value: analysis.carbs_net_g, unit: "g", color: "text-amber-400" },
                      { label: "Fat", value: analysis.fat_g, unit: "g", color: "text-red-400" },
                      { label: "Omega-3", value: analysis.omega3_g, unit: "g", color: "text-purple-400" },
                      { label: "Calories", value: analysis.calories, unit: "kcal", color: "text-gray-300" },
                    ].filter(f => f.value != null).map((f) => (
                      <div key={f.label} className="text-center">
                        <p className={`text-sm font-semibold ${f.color}`}>{f.value}{f.unit}</p>
                        <p className="text-xs text-gray-600">{f.label}</p>
                      </div>
                    ))}
                  </div>
                  {analysis.notes && <p className="text-xs text-gray-500 pt-1">{analysis.notes}</p>}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { setAnalysis(null); setError(null); }}
                    className="flex-1 py-2.5 bg-[#1a1a1a] border border-gray-800 rounded-xl text-sm text-gray-400 hover:text-white transition-colors">
                    Retake
                  </button>
                  <button onClick={handleConfirmPhoto} disabled={loading}
                    className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 rounded-xl text-sm font-semibold text-white transition-colors flex items-center justify-center gap-2">
                    {loading ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : "Save Meal"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Manual tab */}
        {tab === "manual" && (
          <form onSubmit={handleManualSubmit} className="space-y-3">
            <input name="meal_name" value={form.meal_name} onChange={handleChange} required
              placeholder="Meal name (e.g. Chicken salad)"
              className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 text-sm" />
            <div className="grid grid-cols-2 gap-3">
              {([
                { name: "calories", label: "Calories (kcal)" },
                { name: "protein_g", label: "Protein (g)" },
                { name: "fibre_g", label: "Fibre (g)" },
                { name: "carbs_g", label: "Carbs (g)" },
                { name: "fat_g", label: "Fat (g)" },
              ] as Array<{ name: keyof LogMealData; label: string }>).map((field) => (
                <input key={field.name} name={field.name} type="number" min="0" step="0.1"
                  value={(form[field.name] as number | undefined) ?? ""}
                  onChange={handleChange} placeholder={field.label}
                  className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-3 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 text-sm" />
              ))}
            </div>
            <button type="submit" disabled={loading || !form.meal_name.trim()}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2">
              {loading ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Logging…</> : "Log Meal"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default function NutritionPage() {
  const router = useRouter();
  const [data, setData] = useState<NutritionToday | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  async function loadData() {
    try {
      const res = await getNutritionToday();
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load nutrition data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    loadData();
  }, [router]);

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  return (
    <div className="flex flex-col min-h-screen px-4 pt-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Nutrition</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3 py-2 rounded-xl transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
            <path fillRule="evenodd" d="M12 3.75a.75.75 0 0 1 .75.75v6.75h6.75a.75.75 0 0 1 0 1.5h-6.75v6.75a.75.75 0 0 1-1.5 0v-6.75H4.5a.75.75 0 0 1 0-1.5h6.75V4.5a.75.75 0 0 1 .75-.75Z" clipRule="evenodd" />
          </svg>
          Log Meal
        </button>
      </div>

      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {!loading && data && (
        <div className="space-y-4">
          {/* Macro Progress */}
          <div className="bg-[#111111] rounded-2xl p-4 space-y-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Daily Targets</h2>
            <MacroBar
              label="Protein"
              value={data.totals.protein_g}
              target={data.targets.protein_g}
              unit="g"
              color="bg-blue-500"
            />
            <MacroBar
              label="Fibre"
              value={data.totals.fibre_g}
              target={data.targets.fibre_g}
              unit="g"
              color="bg-green-500"
            />
            {data.totals.calories > 0 && (
              <div className="pt-2 border-t border-gray-800">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Total Calories</span>
                  <span className="text-white font-medium">{data.totals.calories.toFixed(0)} kcal</span>
                </div>
              </div>
            )}
          </div>

          {/* Meal List */}
          <div>
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Today&apos;s Meals</h2>
            {data.entries.length === 0 ? (
              <div className="bg-[#111111] rounded-2xl p-6 text-center">
                <p className="text-gray-600 text-sm">No meals logged today</p>
              </div>
            ) : (
              <div className="bg-[#111111] rounded-2xl divide-y divide-gray-800/50">
                {data.entries.map((entry) => (
                  <div key={entry.id} className="px-4 py-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm font-medium text-gray-200">{entry.meal_name}</p>
                        <p className="text-xs text-gray-600">{formatTime(entry.logged_at)}</p>
                      </div>
                      {entry.calories && (
                        <p className="text-sm text-gray-400">{entry.calories} kcal</p>
                      )}
                    </div>
                    <div className="flex gap-3 mt-1.5">
                      {entry.protein_g !== undefined && (
                        <span className="text-xs text-blue-400">P: {entry.protein_g}g</span>
                      )}
                      {entry.fibre_g !== undefined && (
                        <span className="text-xs text-green-400">F: {entry.fibre_g}g</span>
                      )}
                      {entry.carbs_g !== undefined && (
                        <span className="text-xs text-amber-400">C: {entry.carbs_g}g</span>
                      )}
                      {entry.fat_g !== undefined && (
                        <span className="text-xs text-red-400">Fat: {entry.fat_g}g</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {showModal && (
        <LogMealModal
          onClose={() => setShowModal(false)}
          onLogged={() => {
            setLoading(true);
            setError(null);
            loadData();
          }}
        />
      )}
    </div>
  );
}
