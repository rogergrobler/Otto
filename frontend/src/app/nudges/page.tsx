"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { getNudges, acknowledgeNudge } from "@/lib/api";
import type { Nudge } from "@/lib/api";

const nudgeTypeColor: Record<string, string> = {
  daily_checkin: "text-blue-400",
  hrv_alert: "text-red-400",
  sleep_alert: "text-purple-400",
  zone2_reminder: "text-green-400",
  nutrition_reminder: "text-amber-400",
  lab_followup: "text-cyan-400",
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffH = Math.floor(diffMs / 3_600_000);
  if (diffH < 1) return "Just now";
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  if (diffD === 1) return "Yesterday";
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export default function NudgesPage() {
  const router = useRouter();
  const [nudges, setNudges] = useState<Nudge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acking, setAcking] = useState<Set<string>>(new Set());
  const [tab, setTab] = useState<"unread" | "all">("unread");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    getNudges()
      .then(setNudges)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load nudges."))
      .finally(() => setLoading(false));
  }, [router]);

  async function handleAcknowledge(id: string) {
    setAcking((prev) => new Set(prev).add(id));
    try {
      const updated = await acknowledgeNudge(id);
      setNudges((prev) => prev.map((n) => (n.id === id ? updated : n)));
    } catch {
      // silently ignore
    } finally {
      setAcking((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  }

  async function acknowledgeAll() {
    const unread = nudges.filter((n) => !n.acknowledged_at);
    const results = await Promise.allSettled(unread.map((n) => acknowledgeNudge(n.id)));
    results.forEach((r, i) => {
      if (r.status === "fulfilled") {
        setNudges((prev) => prev.map((n) => (n.id === unread[i].id ? r.value : n)));
      }
    });
  }

  const displayed = tab === "unread" ? nudges.filter((n) => !n.acknowledged_at) : nudges;
  const unreadCount = nudges.filter((n) => !n.acknowledged_at).length;

  return (
    <div className="flex flex-col min-h-screen px-4 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold">Nudges</h1>
          {unreadCount > 0 && (
            <p className="text-xs text-gray-500 mt-0.5">{unreadCount} unread</p>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={acknowledgeAll}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-[#111111] rounded-xl p-1 mb-5">
        {(["unread", "all"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2 rounded-lg text-xs font-medium transition-colors capitalize ${
              tab === t
                ? "bg-blue-600 text-white"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {t === "unread" ? `Unread${unreadCount > 0 ? ` (${unreadCount})` : ""}` : "All"}
          </button>
        ))}
      </div>

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

      {!loading && !error && displayed.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-8">
          <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-gray-600">
              <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clipRule="evenodd" />
            </svg>
          </div>
          <p className="text-gray-400 font-medium">
            {tab === "unread" ? "All caught up" : "No nudges yet"}
          </p>
          <p className="text-gray-600 text-sm">
            {tab === "unread"
              ? "No unread nudges. Otto will alert you when there's something to act on."
              : "Otto will send nudges as it analyses your health data."}
          </p>
        </div>
      )}

      {!loading && displayed.length > 0 && (
        <div className="space-y-3 pb-4">
          {displayed.map((nudge) => (
            <div
              key={nudge.id}
              className="rounded-2xl border border-gray-800 bg-[#111111] p-4"
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <span className={`text-[10px] font-medium capitalize ${nudgeTypeColor[nudge.nudge_type] ?? "text-gray-500"}`}>
                  {nudge.nudge_type.replace(/_/g, " ")}
                </span>
                <span className="text-[10px] text-gray-600 flex-shrink-0">
                  {formatDate(nudge.scheduled_at)}
                </span>
              </div>

              <p className="text-sm text-gray-200 leading-relaxed">{nudge.message}</p>

              {!nudge.acknowledged_at && (
                <button
                  onClick={() => handleAcknowledge(nudge.id)}
                  disabled={acking.has(nudge.id)}
                  className="mt-3 text-xs text-blue-400 hover:text-blue-300 disabled:text-gray-600 transition-colors"
                >
                  {acking.has(nudge.id) ? "Marking read…" : "Mark as read"}
                </button>
              )}
              {nudge.acknowledged_at && (
                <p className="mt-3 text-[10px] text-gray-600">Read</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
