"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { getRisk, getLabs, getNutritionToday, getWearables, getNudges } from "@/lib/api";
import type { RiskData, LabResult, NutritionToday, WearableDay, Nudge } from "@/lib/api";
import { HealthScore } from "@/components/health-score";
import { RagDot } from "@/components/rag-dot";

const labStatusColor: Record<string, string> = {
  optimal: "text-green-400",
  normal: "text-gray-400",
  borderline: "text-amber-400",
  high: "text-red-400",
  low: "text-red-400",
  insufficient_data: "text-gray-600",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[#111111] rounded-2xl p-4 space-y-3">
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{title}</h2>
      {children}
    </div>
  );
}

function ProgressBar({ value, max, label, unit }: { value: number; max: number; label: string; unit: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-300">{label}</span>
        <span className="text-gray-400">
          {value.toFixed(0)}<span className="text-gray-600">/{max}{unit}</span>
        </span>
      </div>
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [labs, setLabs] = useState<LabResult[]>([]);
  const [nutrition, setNutrition] = useState<NutritionToday | null>(null);
  const [wearables, setWearables] = useState<WearableDay[]>([]);
  const [nudges, setNudges] = useState<Nudge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    async function loadData() {
      try {
        const [riskData, labsData, nutritionData, wearablesData, nudgesData] =
          await Promise.allSettled([
            getRisk(),
            getLabs(),
            getNutritionToday(),
            getWearables(),
            getNudges(),
          ]);

        if (riskData.status === "fulfilled") setRisk(riskData.value);
        if (labsData.status === "fulfilled") setLabs(labsData.value.slice(0, 3));
        if (nutritionData.status === "fulfilled") setNutrition(nutritionData.value);
        if (wearablesData.status === "fulfilled") setWearables(wearablesData.value.slice(0, 1));
        if (nudgesData.status === "fulfilled") setNudges(nudgesData.value.filter((n) => !n.acknowledged_at));
      } catch {
        setError("Failed to load dashboard data.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [router]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-3">
        <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-500 text-sm">Loading your health data…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-3 px-4">
        <p className="text-red-400 text-center">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-600 rounded-lg text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  const latestWearable = wearables[0];
  const unreadCount = nudges.length;

  return (
    <div className="flex flex-col gap-4 px-4 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Good morning</h1>
          <p className="text-sm text-gray-500">Your health at a glance</p>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={() => router.push("/nudges")}
            className="relative p-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-gray-400">
              <path d="M5.85 3.5a.75.75 0 0 0-1.117-1 9.719 9.719 0 0 0-2.348 4.876.75.75 0 0 0 1.479.248A8.219 8.219 0 0 1 5.85 3.5ZM19.267 2.5a.75.75 0 1 0-1.118 1 8.22 8.22 0 0 1 1.987 4.124.75.75 0 0 0 1.48-.248A9.72 9.72 0 0 0 19.267 2.5Z" />
              <path fillRule="evenodd" d="M12 2.25A6.75 6.75 0 0 0 5.25 9v.75a8.217 8.217 0 0 1-2.119 5.52.75.75 0 0 0 .298 1.206c1.544.57 3.16.99 4.831 1.243a3.75 3.75 0 1 0 7.48 0 24.583 24.583 0 0 0 4.83-1.244.75.75 0 0 0 .298-1.205 8.217 8.217 0 0 1-2.118-5.52V9A6.75 6.75 0 0 0 12 2.25ZM9.75 18c0-.034 0-.067.002-.1a25.05 25.05 0 0 0 4.496 0l.002.1a2.25 2.25 0 1 1-4.5 0Z" clipRule="evenodd" />
            </svg>
            <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-[10px] flex items-center justify-center font-bold">
              {unreadCount}
            </span>
          </button>
        )}
      </div>

      {/* Health Score */}
      <Section title="Health Score">
        <div className="flex flex-col items-center py-2">
          <HealthScore score={risk?.overall_score ?? 0} loading={!risk} />
        </div>
      </Section>

      {/* Domain RAG */}
      {risk && (
        <Section title="Domain Status">
          <div className="flex justify-around py-1">
            <RagDot status={risk.domains.cardiovascular} label="Cardio" size="lg" />
            <RagDot status={risk.domains.metabolic} label="Metabolic" size="lg" />
            <RagDot status={risk.domains.neurological} label="Neuro" size="lg" />
            <RagDot status={risk.domains.cancer} label="Cancer" size="lg" />
          </div>
        </Section>
      )}

      {/* Recent Labs */}
      {labs.length > 0 && (
        <Section title="Recent Labs">
          <div className="space-y-2">
            {labs.map((lab) => (
              <div key={lab.id} className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-200">{lab.marker_name}</p>
                  <p className="text-xs text-gray-600">
                    {new Date(lab.tested_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-medium ${labStatusColor[lab.status]}`}>
                    {lab.value} {lab.unit}
                  </p>
                  <p className="text-xs text-gray-600 capitalize">
                    {lab.status.replace("_", " ")}
                  </p>
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => router.push("/labs")}
            className="w-full text-center text-xs text-blue-400 mt-1"
          >
            View all labs →
          </button>
        </Section>
      )}

      {/* Nutrition */}
      {nutrition && (
        <Section title="Today's Nutrition">
          <ProgressBar
            value={nutrition.totals.protein_g}
            max={nutrition.targets.protein_g}
            label="Protein"
            unit="g"
          />
          <ProgressBar
            value={nutrition.totals.fibre_g}
            max={nutrition.targets.fibre_g}
            label="Fibre"
            unit="g"
          />
          <button
            onClick={() => router.push("/nutrition")}
            className="w-full text-center text-xs text-blue-400 mt-1"
          >
            Log a meal →
          </button>
        </Section>
      )}

      {/* Wearable Snapshot */}
      {latestWearable && (
        <Section title="Today's Wearable Data">
          <div className="grid grid-cols-3 gap-3">
            {latestWearable.hrv_ms !== undefined && (
              <div className="text-center">
                <p className="text-2xl font-bold text-green-400">{latestWearable.hrv_ms}</p>
                <p className="text-xs text-gray-500">HRV (ms)</p>
              </div>
            )}
            {latestWearable.sleep_hours !== undefined && (
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-400">{latestWearable.sleep_hours?.toFixed(1)}</p>
                <p className="text-xs text-gray-500">Sleep (hrs)</p>
              </div>
            )}
            {latestWearable.recovery_score !== undefined && (
              <div className="text-center">
                <p className="text-2xl font-bold text-amber-400">{latestWearable.recovery_score}</p>
                <p className="text-xs text-gray-500">Recovery</p>
              </div>
            )}
          </div>
          <button
            onClick={() => router.push("/wearables")}
            className="w-full text-center text-xs text-blue-400 mt-1"
          >
            View 7-day history →
          </button>
        </Section>
      )}
    </div>
  );
}
