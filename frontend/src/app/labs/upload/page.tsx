"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { createLab } from "@/lib/api";

const COMMON_MARKERS = [
  "Total Cholesterol",
  "LDL Cholesterol",
  "HDL Cholesterol",
  "Triglycerides",
  "Fasting Glucose",
  "HbA1c",
  "hsCRP",
  "Testosterone",
  "Free Testosterone",
  "TSH",
  "Free T4",
  "Vitamin D",
  "Vitamin B12",
  "Ferritin",
  "Haemoglobin",
  "eGFR",
  "ALT",
  "AST",
  "ApoB",
  "Lp(a)",
];

export default function LabUploadPage() {
  const router = useRouter();
  const [marker, setMarker] = useState("");
  const [customMarker, setCustomMarker] = useState("");
  const [value, setValue] = useState("");
  const [unit, setUnit] = useState("");
  const [testedAt, setTestedAt] = useState(() => new Date().toISOString().slice(0, 10));
  const [referenceRange, setReferenceRange] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  const markerName = marker === "__custom__" ? customMarker : marker;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!markerName || !value || !unit || !testedAt) return;

    setSaving(true);
    setError(null);
    try {
      await createLab({
        marker_name: markerName,
        value: parseFloat(value),
        unit,
        tested_at: new Date(testedAt).toISOString(),
        reference_range: referenceRange || undefined,
      });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save lab result.");
    } finally {
      setSaving(false);
    }
  }

  function addAnother() {
    setMarker("");
    setCustomMarker("");
    setValue("");
    setUnit("");
    setReferenceRange("");
    setSaved(false);
  }

  if (saved) {
    return (
      <div className="flex flex-col min-h-screen items-center justify-center px-6 text-center gap-5">
        <div className="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-green-400">
            <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clipRule="evenodd" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-bold text-white">Result Saved</h2>
          <p className="text-gray-500 text-sm mt-1">
            <span className="text-white font-medium">{markerName}</span> added to your lab history.
          </p>
        </div>
        <div className="flex gap-3 w-full max-w-xs">
          <button
            onClick={addAnother}
            className="flex-1 py-3 bg-[#1a1a1a] border border-gray-800 rounded-xl text-sm font-medium hover:bg-gray-800 transition-colors"
          >
            Add Another
          </button>
          <button
            onClick={() => router.push("/labs")}
            className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl text-sm font-medium transition-colors"
          >
            View Labs
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen px-4 pt-6">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.back()} className="text-gray-500 hover:text-white transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
            <path fillRule="evenodd" d="M7.72 12.53a.75.75 0 0 1 0-1.06l7.5-7.5a.75.75 0 1 1 1.06 1.06L9.31 12l6.97 6.97a.75.75 0 1 1-1.06 1.06l-7.5-7.5Z" clipRule="evenodd" />
          </svg>
        </button>
        <h1 className="text-xl font-bold">Add Lab Result</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Marker selection */}
        <div>
          <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">
            Marker
          </label>
          <select
            value={marker}
            onChange={(e) => setMarker(e.target.value)}
            required
            className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors appearance-none"
          >
            <option value="" disabled>Select a marker…</option>
            {COMMON_MARKERS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
            <option value="__custom__">Other (type below)</option>
          </select>
        </div>

        {marker === "__custom__" && (
          <div>
            <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">
              Marker Name
            </label>
            <input
              type="text"
              value={customMarker}
              onChange={(e) => setCustomMarker(e.target.value)}
              placeholder="e.g. Homocysteine"
              required
              className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        )}

        {/* Value + Unit */}
        <div className="flex gap-3">
          <div className="flex-1">
            <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">
              Value
            </label>
            <input
              type="number"
              step="any"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="e.g. 5.2"
              required
              className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
          <div className="w-28">
            <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">
              Unit
            </label>
            <input
              type="text"
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              placeholder="mmol/L"
              required
              className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        {/* Tested At */}
        <div>
          <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">
            Test Date
          </label>
          <input
            type="date"
            value={testedAt}
            onChange={(e) => setTestedAt(e.target.value)}
            required
            className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        {/* Reference Range */}
        <div>
          <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">
            Reference Range <span className="text-gray-700 normal-case">(optional)</span>
          </label>
          <input
            type="text"
            value={referenceRange}
            onChange={(e) => setReferenceRange(e.target.value)}
            placeholder="e.g. 3.0 – 5.5"
            className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={saving || !markerName || !value || !unit}
          className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-800 disabled:text-gray-600 rounded-xl text-sm font-semibold transition-colors mt-2"
        >
          {saving ? "Saving…" : "Save Result"}
        </button>
      </form>

      <p className="text-xs text-gray-600 text-center mt-6 px-4">
        Otto will automatically score and interpret this result against evidence-based reference ranges.
      </p>
    </div>
  );
}
