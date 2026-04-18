"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { getGoals, createGoal } from "@/lib/api";
import type { Goal, CreateGoalData } from "@/lib/api";

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

const DOMAINS: Array<{ value: CreateGoalData["domain"]; label: string }> = [
  { value: "cardiovascular", label: "Cardiovascular" },
  { value: "metabolic", label: "Metabolic" },
  { value: "neurological", label: "Neurological" },
  { value: "cancer_prevention", label: "Cancer Prevention" },
  { value: "nutrition", label: "Nutrition" },
  { value: "training", label: "Training" },
  { value: "body_composition", label: "Body Composition" },
  { value: "sleep", label: "Sleep" },
  { value: "supplements", label: "Supplements" },
  { value: "general", label: "General" },
];

function CreateGoalModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form, setForm] = useState<CreateGoalData>({
    domain: "general",
    goal_text: "",
    target_metric: "",
    deadline: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.goal_text.trim()) return;
    setError(null);
    setLoading(true);
    try {
      await createGoal({
        domain: form.domain,
        goal_text: form.goal_text.trim(),
        target_metric: form.target_metric?.trim() || undefined,
        deadline: form.deadline || undefined,
      });
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create goal.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60">
      <div className="w-full max-w-md bg-[#111111] rounded-t-3xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">New Goal</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M5.47 5.47a.75.75 0 0 1 1.06 0L12 10.94l5.47-5.47a.75.75 0 1 1 1.06 1.06L13.06 12l5.47 5.47a.75.75 0 1 1-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 0 1-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {error && (
          <p className="text-red-400 text-sm bg-red-500/10 px-3 py-2 rounded-lg">{error}</p>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1.5">Domain</label>
            <select
              value={form.domain}
              onChange={(e) => setForm((p) => ({ ...p, domain: e.target.value as CreateGoalData["domain"] }))}
              className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500 appearance-none"
            >
              {DOMAINS.map((d) => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1.5">Goal</label>
            <textarea
              value={form.goal_text}
              onChange={(e) => setForm((p) => ({ ...p, goal_text: e.target.value }))}
              required
              rows={3}
              placeholder="e.g. Reduce LDL to below 2.0 mmol/L by July"
              className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 text-sm resize-none"
            />
          </div>

          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1.5">Target metric <span className="text-gray-700 normal-case">(optional)</span></label>
            <input
              type="text"
              value={form.target_metric}
              onChange={(e) => setForm((p) => ({ ...p, target_metric: e.target.value }))}
              placeholder="e.g. LDL &lt; 2.0 mmol/L"
              className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 text-sm"
            />
          </div>

          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1.5">Deadline <span className="text-gray-700 normal-case">(optional)</span></label>
            <input
              type="date"
              value={form.deadline}
              onChange={(e) => setForm((p) => ({ ...p, deadline: e.target.value }))}
              className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !form.goal_text.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : "Create Goal"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function GoalsPage() {
  const router = useRouter();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  function loadGoals() {
    setLoading(true);
    setError(null);
    getGoals()
      .then(setGoals)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load goals."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    loadGoals();
  }, [router]);

  const activeGoals = goals.filter((g) => g.status === "active");
  const otherGoals = goals.filter((g) => g.status !== "active");

  return (
    <div className="flex flex-col min-h-screen px-4 pt-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Health Goals</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3 py-2 rounded-xl transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
            <path fillRule="evenodd" d="M12 3.75a.75.75 0 0 1 .75.75v6.75h6.75a.75.75 0 0 1 0 1.5h-6.75v6.75a.75.75 0 0 1-1.5 0v-6.75H4.5a.75.75 0 0 1 0-1.5h6.75V4.5a.75.75 0 0 1 .75-.75Z" clipRule="evenodd" />
          </svg>
          Add Goal
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

      {showCreate && (
        <CreateGoalModal
          onClose={() => setShowCreate(false)}
          onCreated={loadGoals}
        />
      )}
    </div>
  );
}
