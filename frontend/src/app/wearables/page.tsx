"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { getWearables } from "@/lib/api";
import type { WearableDay } from "@/lib/api";

function fmt(val: number | undefined, decimals = 0): string {
  if (val === undefined || val === null) return "—";
  return val.toFixed(decimals);
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
}

function HrvIndicator({ hrv }: { hrv: number | undefined }) {
  if (hrv === undefined) return <span className="text-gray-600">—</span>;
  const color = hrv >= 60 ? "text-green-400" : hrv >= 40 ? "text-amber-400" : "text-red-400";
  return <span className={color}>{hrv.toFixed(0)}</span>;
}

function RecoveryIndicator({ score }: { score: number | undefined }) {
  if (score === undefined) return <span className="text-gray-600">—</span>;
  const color = score >= 67 ? "text-green-400" : score >= 34 ? "text-amber-400" : "text-red-400";
  return <span className={color}>{score.toFixed(0)}</span>;
}

function SleepIndicator({ hrs }: { hrs: number | undefined }) {
  if (hrs === undefined) return <span className="text-gray-600">—</span>;
  const color = hrs >= 7 ? "text-green-400" : hrs >= 6 ? "text-amber-400" : "text-red-400";
  return <span className={color}>{hrs.toFixed(1)}</span>;
}

// Summary metric card
function MetricCard({ label, value, unit, color }: { label: string; value: string; unit: string; color: string }) {
  return (
    <div className="bg-[#111111] rounded-2xl p-4 text-center">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{unit}</p>
      <p className="text-xs text-gray-600 mt-1">{label}</p>
    </div>
  );
}

export default function WearablesPage() {
  const router = useRouter();
  const [days, setDays] = useState<WearableDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    getWearables()
      .then((data) => {
        // Sort desc, take last 7
        const sorted = [...data]
          .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
          .slice(0, 7);
        setDays(sorted);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load wearable data.")
      )
      .finally(() => setLoading(false));
  }, [router]);

  // Compute averages for summary cards
  const withHrv = days.filter((d) => d.hrv_ms !== undefined);
  const withSleep = days.filter((d) => d.sleep_hours !== undefined);
  const withRecovery = days.filter((d) => d.recovery_score !== undefined);
  const withSteps = days.filter((d) => d.steps !== undefined);

  const avgHrv =
    withHrv.length > 0
      ? withHrv.reduce((s, d) => s + d.hrv_ms!, 0) / withHrv.length
      : undefined;
  const avgSleep =
    withSleep.length > 0
      ? withSleep.reduce((s, d) => s + d.sleep_hours!, 0) / withSleep.length
      : undefined;
  const avgRecovery =
    withRecovery.length > 0
      ? withRecovery.reduce((s, d) => s + d.recovery_score!, 0) / withRecovery.length
      : undefined;
  const avgSteps =
    withSteps.length > 0
      ? withSteps.reduce((s, d) => s + d.steps!, 0) / withSteps.length
      : undefined;

  return (
    <div className="flex flex-col min-h-screen px-4 pt-6">
      <h1 className="text-xl font-bold mb-6">Wearable Data</h1>

      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 mb-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {!loading && !error && days.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-8">
          <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-gray-600">
              <path d="M11.25 5.337c0-.355-.186-.676-.401-.959a1.647 1.647 0 0 1-.349-1.003c0-1.036 1.007-1.875 2.25-1.875S15 2.34 15 3.375c0 .369-.128.713-.349 1.003-.215.283-.401.604-.401.959 0 .332.278.598.61.578 1.91-.114 3.79-.342 5.632-.676a.75.75 0 0 1 .878.645 49.17 49.17 0 0 1 .376 5.452.657.657 0 0 1-.66.664c-.354 0-.675-.186-.958-.401a1.647 1.647 0 0 0-1.003-.349c-1.035 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401.31 0 .557.262.534.571a48.774 48.774 0 0 1-.595 4.845.75.75 0 0 1-.61.61c-1.82.317-3.673.533-5.555.642a.58.58 0 0 1-.611-.581c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.035-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959a.641.641 0 0 1-.658.643 49.118 49.118 0 0 1-4.708-.36.75.75 0 0 1-.645-.878c.293-1.614.504-3.257.629-4.924A.53.53 0 0 0 5.337 15c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.036 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.369 0 .713.128 1.003.349.283.215.604.401.959.401a.656.656 0 0 0 .659-.663 47.703 47.703 0 0 0-.31-4.82.75.75 0 0 1 .83-.832c1.343.155 2.703.254 4.077.294a.64.64 0 0 0 .657-.642Z" />
            </svg>
          </div>
          <p className="text-gray-400 font-medium">No wearable data yet</p>
          <p className="text-gray-600 text-sm">Connect your device to start tracking.</p>
        </div>
      )}

      {!loading && days.length > 0 && (
        <div className="space-y-5">
          {/* 7-day averages */}
          <div>
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              7-Day Averages
            </h2>
            <div className="grid grid-cols-2 gap-3">
              <MetricCard
                label="Avg HRV"
                value={fmt(avgHrv, 0)}
                unit="ms"
                color={avgHrv !== undefined ? (avgHrv >= 60 ? "text-green-400" : avgHrv >= 40 ? "text-amber-400" : "text-red-400") : "text-gray-500"}
              />
              <MetricCard
                label="Avg Sleep"
                value={fmt(avgSleep, 1)}
                unit="hours"
                color={avgSleep !== undefined ? (avgSleep >= 7 ? "text-green-400" : avgSleep >= 6 ? "text-amber-400" : "text-red-400") : "text-gray-500"}
              />
              <MetricCard
                label="Avg Recovery"
                value={fmt(avgRecovery, 0)}
                unit="/ 100"
                color={avgRecovery !== undefined ? (avgRecovery >= 67 ? "text-green-400" : avgRecovery >= 34 ? "text-amber-400" : "text-red-400") : "text-gray-500"}
              />
              <MetricCard
                label="Avg Steps"
                value={avgSteps !== undefined ? Math.round(avgSteps).toLocaleString() : "—"}
                unit="steps"
                color="text-blue-400"
              />
            </div>
          </div>

          {/* Daily table */}
          <div>
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Daily Log
            </h2>
            <div className="bg-[#111111] rounded-2xl overflow-hidden">
              {/* Table header */}
              <div className="grid grid-cols-5 px-4 py-2 border-b border-gray-800">
                {["Date", "Sleep", "HRV", "Rec.", "Steps"].map((h) => (
                  <span key={h} className="text-[10px] text-gray-600 font-medium text-center first:text-left">
                    {h}
                  </span>
                ))}
              </div>
              {/* Rows */}
              {days.map((day) => (
                <div
                  key={day.date}
                  className="grid grid-cols-5 px-4 py-3 border-b border-gray-800/50 last:border-0"
                >
                  <span className="text-xs text-gray-400">{formatDate(day.date)}</span>
                  <div className="text-xs text-center">
                    <SleepIndicator hrs={day.sleep_hours} />
                  </div>
                  <div className="text-xs text-center">
                    <HrvIndicator hrv={day.hrv_ms} />
                  </div>
                  <div className="text-xs text-center">
                    <RecoveryIndicator score={day.recovery_score} />
                  </div>
                  <span className="text-xs text-center text-gray-300">
                    {day.steps !== undefined ? day.steps.toLocaleString() : "—"}
                  </span>
                </div>
              ))}
            </div>

            {/* Zone 2 section if any data */}
            {days.some((d) => d.zone2_mins !== undefined) && (
              <div className="mt-3 bg-[#111111] rounded-2xl px-4 py-3">
                <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Zone 2 Minutes</h3>
                <div className="space-y-1.5">
                  {days
                    .filter((d) => d.zone2_mins !== undefined)
                    .map((day) => (
                      <div key={day.date} className="flex justify-between text-sm">
                        <span className="text-gray-400 text-xs">{formatDate(day.date)}</span>
                        <span className="text-blue-400 text-xs font-medium">{day.zone2_mins} min</span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
