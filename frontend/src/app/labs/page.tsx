"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { getLabs } from "@/lib/api";
import type { LabResult } from "@/lib/api";

const statusConfig: Record<
  string,
  { label: string; bg: string; text: string }
> = {
  optimal: { label: "Optimal", bg: "bg-green-500/15", text: "text-green-400" },
  normal: { label: "Normal", bg: "bg-gray-500/15", text: "text-gray-400" },
  borderline: { label: "Borderline", bg: "bg-amber-500/15", text: "text-amber-400" },
  high: { label: "High", bg: "bg-red-500/15", text: "text-red-400" },
  low: { label: "Low", bg: "bg-red-500/15", text: "text-red-400" },
  insufficient_data: { label: "No Data", bg: "bg-gray-800", text: "text-gray-600" },
};

function groupByDate(labs: LabResult[]): Record<string, LabResult[]> {
  return labs.reduce<Record<string, LabResult[]>>((acc, lab) => {
    const date = new Date(lab.tested_at).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    if (!acc[date]) acc[date] = [];
    acc[date].push(lab);
    return acc;
  }, {});
}

export default function LabsPage() {
  const router = useRouter();
  const [labs, setLabs] = useState<LabResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    getLabs()
      .then(setLabs)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load labs."))
      .finally(() => setLoading(false));
  }, [router]);

  const grouped = groupByDate(labs);
  const dates = Object.keys(grouped).sort(
    (a, b) => new Date(b).getTime() - new Date(a).getTime()
  );

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-6 pb-4">
        <h1 className="text-xl font-bold">Lab Results</h1>
        <button
          onClick={() => router.push("/labs/upload")}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3 py-2 rounded-xl transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
            <path fillRule="evenodd" d="M11.47 2.47a.75.75 0 0 1 1.06 0l4.5 4.5a.75.75 0 0 1-1.06 1.06l-3.22-3.22V16.5a.75.75 0 0 1-1.5 0V4.81L8.03 8.03a.75.75 0 0 1-1.06-1.06l4.5-4.5ZM3 15.75a.75.75 0 0 1 .75.75v2.25a1.5 1.5 0 0 0 1.5 1.5h13.5a1.5 1.5 0 0 0 1.5-1.5V16.5a.75.75 0 0 1 1.5 0v2.25a3 3 0 0 1-3 3H5.25a3 3 0 0 1-3-3V16.5a.75.75 0 0 1 .75-.75Z" clipRule="evenodd" />
          </svg>
          Add Result
        </button>
      </div>

      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="px-4">
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && labs.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-8">
          <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-gray-600">
              <path fillRule="evenodd" d="M10.5 3.798v5.02a3 3 0 0 1-.879 2.121l-2.377 2.377a9.845 9.845 0 0 1 5.091 1.013 8.315 8.315 0 0 0 5.713.636l.285-.071-3.954-3.955a3 3 0 0 1-.879-2.121v-5.02a23.614 23.614 0 0 0-3 0Zm4.5.138a.75.75 0 0 0 .093-1.495A24.837 24.837 0 0 0 12 2.25a25.048 25.048 0 0 0-3.093.191A.75.75 0 0 0 9 3.938v4.88a1.5 1.5 0 0 1-.44 1.06l-6.293 6.294c-1.62 1.621-.903 4.475 1.471 4.88 2.686.46 5.447.698 8.262.698 2.816 0 5.576-.239 8.262-.698 2.374-.405 3.092-3.259 1.47-4.88L15.44 9.879A1.5 1.5 0 0 1 15 8.818V3.938Z" clipRule="evenodd" />
            </svg>
          </div>
          <p className="text-gray-400 font-medium">No lab results yet</p>
          <p className="text-gray-600 text-sm">Upload your blood work to get started.</p>
        </div>
      )}

      {!loading && labs.length > 0 && (
        <div className="px-4 space-y-6 pb-4">
          {dates.map((date) => (
            <div key={date}>
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                {date}
              </h2>
              <div className="bg-[#111111] rounded-2xl divide-y divide-gray-800/50">
                {grouped[date].map((lab) => {
                  const config = statusConfig[lab.status] ?? statusConfig.normal;
                  return (
                    <div key={lab.id} className="flex items-center justify-between px-4 py-3">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-200 font-medium truncate">
                          {lab.marker_name}
                        </p>
                        {lab.reference_range && (
                          <p className="text-xs text-gray-600">
                            Ref: {lab.reference_range}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <p className="text-sm font-medium text-white">
                          {lab.value} {lab.unit}
                        </p>
                        <span
                          className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${config.bg} ${config.text}`}
                        >
                          {config.label}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
