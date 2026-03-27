"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { getGoals } from "@/lib/api";
import type { Goal } from "@/lib/api";

const domainConfig: Record<string, { label: string; color: string; bg: string }> = {
  cardiovascular: { label: "Cardiovascular", color: "text-red-400", bg: "bg-red-500/10" },
  metabolic: { label: "Metabolic", color: "text-amber-400", bg: "bg-amber-500/10" },
  neurological: { label: "Neurological", color: "text-purple-400", bg: "bg-purple-500/10" },
  cancer: { label: "Cancer Prevention", color: "text-blue-400", bg: "bg-blue-500/10" },
  general: { label: "General", color: "text-gray-400", bg: "bg-gray-500/10" },
};

const statusConfig: Record<string, { label: string; color: string }> = {
  active: { label: "Active", color: "text-green-400" },
  achieved: { label: "Achieved", color: "text-blue-400" },
  paused: { label: "Paused", color: "text-gray-500" },
};

function GoalCard({ goal }: { goal: Goal }) {
  const domain = domainConfig[goal.domain] ?? domainConfig.general;
  const status = statusConfig[goal.status] ?? statusConfig.active;

  const hasProgress =
    goal.current_value !== undefined && goal.target_value !== undefined;
  const pct = hasProgress
    ? Math.min(100, (goal.current_value! / goal.target_value!) * 100)
    : null;

  const deadline = goal.deadline
    ? new Date(goal.deadline).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : null;

  return (
    <div className="bg-[#111111] rounded-2xl p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className={`text-[11px] font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${domain.bg} ${domain.color}`}
          >
            {domain.label}
          </span>
        </div>
        <span className={`text-xs font-medium flex-shrink-0 ${status.color}`}>
          {status.label}
        </span>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-white leading-snug">{goal.title}</h3>
        {goal.description && (
          <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{goal.description}</p>
        )}
      </div>

      {hasProgress && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-gray-400">
            <span>
              Current:{" "}
              <span className="text-white font-medium">
                {goal.current_value} {goal.unit}
              </span>
            </span>
            <span>
              Target:{" "}
              <span className="text-white font-medium">
                {goal.target_value} {goal.unit}
              </span>
            </span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-xs text-gray-600">{pct?.toFixed(0)}% of target</p>
        </div>
      )}

      {deadline && (
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5">
            <path fillRule="evenodd" d="M6.75 2.25A.75.75 0 0 1 7.5 3v1.5h9V3A.75.75 0 0 1 18 3v1.5h.75a3 3 0 0 1 3 3v11.25a3 3 0 0 1-3 3H5.25a3 3 0 0 1-3-3V7.5a3 3 0 0 1 3-3H6V3a.75.75 0 0 1 .75-.75Zm13.5 9a1.5 1.5 0 0 0-1.5-1.5H5.25a1.5 1.5 0 0 0-1.5 1.5v7.5a1.5 1.5 0 0 0 1.5 1.5h13.5a1.5 1.5 0 0 0 1.5-1.5v-7.5Z" clipRule="evenodd" />
          </svg>
          Deadline: {deadline}
        </div>
      )}
    </div>
  );
}

export default function GoalsPage() {
  const router = useRouter();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    getGoals()
      .then(setGoals)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load goals."))
      .finally(() => setLoading(false));
  }, [router]);

  const activeGoals = goals.filter((g) => g.status === "active");
  const otherGoals = goals.filter((g) => g.status !== "active");

  return (
    <div className="flex flex-col min-h-screen px-4 pt-6">
      <h1 className="text-xl font-bold mb-6">Health Goals</h1>

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

      {!loading && !error && goals.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-8">
          <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-gray-600">
              <path fillRule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25Zm-.53 14.03a.75.75 0 0 0 1.06 0l3-3a.75.75 0 1 0-1.06-1.06l-1.72 1.72V8.25a.75.75 0 0 0-1.5 0v5.69l-1.72-1.72a.75.75 0 0 0-1.06 1.06l3 3Z" clipRule="evenodd" />
            </svg>
          </div>
          <p className="text-gray-400 font-medium">No goals set yet</p>
          <p className="text-gray-600 text-sm">
            Chat with Otto to create personalised health goals.
          </p>
          <button
            onClick={() => router.push("/chat")}
            className="mt-2 px-5 py-2.5 bg-blue-600 rounded-xl text-sm font-medium"
          >
            Open Chat
          </button>
        </div>
      )}

      {!loading && goals.length > 0 && (
        <div className="space-y-5">
          {activeGoals.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Active ({activeGoals.length})
              </h2>
              {activeGoals.map((goal) => (
                <GoalCard key={goal.id} goal={goal} />
              ))}
            </div>
          )}

          {otherGoals.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Other
              </h2>
              {otherGoals.map((goal) => (
                <GoalCard key={goal.id} goal={goal} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
