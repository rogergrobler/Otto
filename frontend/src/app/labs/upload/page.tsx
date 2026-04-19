"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { uploadLabPDF, confirmLabOCR, createLab } from "@/lib/api";
import type { LabOCRResult, LabOCRMarker } from "@/lib/api";

const COMMON_MARKERS = [
  "Total Cholesterol","LDL Cholesterol","HDL Cholesterol","Triglycerides",
  "Fasting Glucose","HbA1c","hsCRP","Testosterone","Free Testosterone",
  "TSH","Free T4","Vitamin D","Vitamin B12","Ferritin","Haemoglobin",
  "eGFR","ALT","AST","ApoB","Lp(a)",
];

// ── PDF Upload flow ────────────────────────────────────────────────────────────

function PdfUploadFlow({ onDone }: { onDone: () => void }) {
  const [stage, setStage] = useState<"pick" | "scanning" | "review">("pick");
  const [ocr, setOcr] = useState<LabOCRResult | null>(null);
  const [markers, setMarkers] = useState<LabOCRMarker[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setStage("scanning");
    try {
      const result = await uploadLabPDF(file);
      setOcr(result);
      setMarkers(result.markers);
      setStage("review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to extract lab data.");
      setStage("pick");
    }
  }

  function updateMarker(idx: number, field: keyof LabOCRMarker, val: string) {
    setMarkers((prev) => prev.map((m, i) => i === idx ? { ...m, [field]: val } : m));
  }

  function removeMarker(idx: number) {
    setMarkers((prev) => prev.filter((_, i) => i !== idx));
  }

  async function handleConfirm() {
    if (!ocr) return;
    setSaving(true);
    setError(null);
    try {
      await confirmLabOCR({ ...ocr, markers });
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save results.");
    } finally {
      setSaving(false);
    }
  }

  if (stage === "pick") {
    return (
      <div className="space-y-4">
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}
        <button
          onClick={() => fileRef.current?.click()}
          className="w-full h-40 border-2 border-dashed border-gray-700 rounded-2xl flex flex-col items-center justify-center gap-3 hover:border-blue-500 hover:bg-blue-500/5 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-gray-600">
            <path fillRule="evenodd" d="M5.625 1.5H9a3.75 3.75 0 0 1 3.75 3.75v1.875c0 1.036.84 1.875 1.875 1.875H16.5a3.75 3.75 0 0 1 3.75 3.75v7.875c0 1.035-.84 1.875-1.875 1.875H5.625a1.875 1.875 0 0 1-1.875-1.875V3.375c0-1.036.84-1.875 1.875-1.875Zm5.845 17.03a.75.75 0 0 0 1.06 0l3-3a.75.75 0 1 0-1.06-1.06l-1.72 1.72V12a.75.75 0 0 0-1.5 0v4.19l-1.72-1.72a.75.75 0 0 0-1.06 1.06l3 3Z" clipRule="evenodd" />
          </svg>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-300">Tap to upload PDF</p>
            <p className="text-xs text-gray-600 mt-0.5">PathCare, Lancet, Dischem — any lab report</p>
          </div>
        </button>
        <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleFile} />
        <p className="text-xs text-gray-600 text-center">
          Claude Vision reads the PDF and extracts all markers. Takes ~6 seconds.
        </p>
      </div>
    );
  }

  if (stage === "scanning") {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <div className="w-12 h-12 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Reading your lab report…</p>
        <p className="text-gray-600 text-xs">This takes about 6 seconds</p>
      </div>
    );
  }

  // Review stage
  return (
    <div className="space-y-4">
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl px-4 py-3">
        <p className="text-blue-400 text-sm font-medium">
          {markers.length} marker{markers.length !== 1 ? "s" : ""} extracted
          {ocr?.lab_name ? ` from ${ocr.lab_name}` : ""}
          {ocr?.test_date ? ` · ${ocr.test_date}` : ""}
        </p>
        <p className="text-gray-500 text-xs mt-0.5">Review and remove any errors before saving.</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      <div className="space-y-2">
        {markers.map((m, idx) => (
          <div key={idx} className="bg-[#111111] rounded-xl px-4 py-3 flex items-center justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate">{m.marker_name}</p>
              <p className="text-xs text-gray-500">
                {m.value ?? m.value_text ?? "—"} {m.unit}
                {m.flag ? <span className={`ml-1.5 ${m.flag === "high" || m.flag === "low" ? "text-red-400" : "text-gray-500"}`}>{m.flag}</span> : null}
              </p>
            </div>
            <button
              onClick={() => removeMarker(idx)}
              className="text-gray-700 hover:text-red-400 transition-colors flex-shrink-0"
              aria-label="Remove"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M5.47 5.47a.75.75 0 0 1 1.06 0L12 10.94l5.47-5.47a.75.75 0 1 1 1.06 1.06L13.06 12l5.47 5.47a.75.75 0 1 1-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 0 1-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        ))}
      </div>

      <button
        onClick={handleConfirm}
        disabled={saving || markers.length === 0}
        className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-800 disabled:text-gray-600 rounded-xl text-sm font-semibold transition-colors"
      >
        {saving ? "Saving…" : `Save ${markers.length} result${markers.length !== 1 ? "s" : ""}`}
      </button>
    </div>
  );
}

// ── Manual entry flow ──────────────────────────────────────────────────────────

function ManualEntryFlow({ onDone }: { onDone: () => void }) {
  const [marker, setMarker] = useState("");
  const [customMarker, setCustomMarker] = useState("");
  const [value, setValue] = useState("");
  const [unit, setUnit] = useState("");
  const [testedAt, setTestedAt] = useState(() => new Date().toISOString().slice(0, 10));
  const [referenceRange, setReferenceRange] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save lab result.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">Marker</label>
        <select value={marker} onChange={(e) => setMarker(e.target.value)} required
          className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors appearance-none">
          <option value="" disabled>Select a marker…</option>
          {COMMON_MARKERS.map((m) => <option key={m} value={m}>{m}</option>)}
          <option value="__custom__">Other (type below)</option>
        </select>
      </div>

      {marker === "__custom__" && (
        <div>
          <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">Marker Name</label>
          <input type="text" value={customMarker} onChange={(e) => setCustomMarker(e.target.value)}
            placeholder="e.g. Homocysteine" required
            className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors" />
        </div>
      )}

      <div className="flex gap-3">
        <div className="flex-1">
          <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">Value</label>
          <input type="number" step="any" value={value} onChange={(e) => setValue(e.target.value)}
            placeholder="e.g. 5.2" required
            className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors" />
        </div>
        <div className="w-28">
          <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">Unit</label>
          <input type="text" value={unit} onChange={(e) => setUnit(e.target.value)}
            placeholder="mmol/L" required
            className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors" />
        </div>
      </div>

      <div>
        <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">Test Date</label>
        <input type="date" value={testedAt} onChange={(e) => setTestedAt(e.target.value)} required
          className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors" />
      </div>

      <div>
        <label className="text-xs text-gray-500 font-medium uppercase tracking-wider block mb-2">
          Reference Range <span className="text-gray-700 normal-case">(optional)</span>
        </label>
        <input type="text" value={referenceRange} onChange={(e) => setReferenceRange(e.target.value)}
          placeholder="e.g. 3.0 – 5.5"
          className="w-full bg-[#111111] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors" />
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      <button type="submit" disabled={saving || !markerName || !value || !unit}
        className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-800 disabled:text-gray-600 rounded-xl text-sm font-semibold transition-colors mt-2">
        {saving ? "Saving…" : "Save Result"}
      </button>
    </form>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LabUploadPage() {
  const router = useRouter();
  const [tab, setTab] = useState<"pdf" | "manual">("pdf");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  if (saved) {
    return (
      <div className="flex flex-col min-h-screen items-center justify-center px-6 text-center gap-5">
        <div className="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-green-400">
            <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clipRule="evenodd" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-bold text-white">Results Saved</h2>
          <p className="text-gray-500 text-sm mt-1">Otto has your latest lab data.</p>
        </div>
        <div className="flex gap-3 w-full max-w-xs">
          <button onClick={() => { setSaved(false); setTab("pdf"); }}
            className="flex-1 py-3 bg-[#1a1a1a] border border-gray-800 rounded-xl text-sm font-medium hover:bg-gray-800 transition-colors">
            Add More
          </button>
          <button onClick={() => router.push("/labs")}
            className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl text-sm font-medium transition-colors">
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
        <h1 className="text-xl font-bold">Add Lab Results</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 bg-[#111111] rounded-xl p-1">
        {(["pdf", "manual"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${tab === t ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-300"}`}>
            {t === "pdf" ? "Upload PDF" : "Manual Entry"}
          </button>
        ))}
      </div>

      {tab === "pdf"
        ? <PdfUploadFlow onDone={() => setSaved(true)} />
        : <ManualEntryFlow onDone={() => setSaved(true)} />
      }
    </div>
  );
}
