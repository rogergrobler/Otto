"use client";

interface HealthScoreProps {
  score: number;
  loading?: boolean;
}

function getScoreColor(score: number): string {
  if (score >= 75) return "text-green-400";
  if (score >= 50) return "text-amber-400";
  return "text-red-400";
}

function getScoreLabel(score: number): string {
  if (score >= 80) return "Excellent";
  if (score >= 65) return "Good";
  if (score >= 50) return "Fair";
  if (score >= 35) return "Poor";
  return "Critical";
}

export function HealthScore({ score, loading }: HealthScoreProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center gap-2">
        <div className="w-28 h-28 rounded-full bg-gray-800 animate-pulse" />
        <div className="w-16 h-4 bg-gray-800 rounded animate-pulse" />
      </div>
    );
  }

  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const colorClass = getScoreColor(clamped);
  const label = getScoreLabel(clamped);

  // SVG circle progress
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const dashoffset = circumference - (clamped / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-32 h-32">
        <svg
          className="w-full h-full -rotate-90"
          viewBox="0 0 120 120"
        >
          {/* Track */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="#1f2937"
            strokeWidth="8"
          />
          {/* Progress */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke={clamped >= 75 ? "#22c55e" : clamped >= 50 ? "#f59e0b" : "#ef4444"}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashoffset}
            className="transition-all duration-700"
          />
        </svg>
        {/* Score number */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${colorClass}`}>{clamped}</span>
          <span className="text-xs text-gray-500">/100</span>
        </div>
      </div>
      <span className={`text-sm font-medium ${colorClass}`}>{label}</span>
    </div>
  );
}
