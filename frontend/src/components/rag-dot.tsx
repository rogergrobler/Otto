"use client";

type RagStatus = "green" | "amber" | "red" | "insufficient_data";

interface RagDotProps {
  status: RagStatus;
  label: string;
  size?: "sm" | "md" | "lg";
}

const statusColors: Record<RagStatus, string> = {
  green: "bg-green-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
  insufficient_data: "bg-gray-700",
};

const statusLabels: Record<RagStatus, string> = {
  green: "Optimal",
  amber: "Borderline",
  red: "At Risk",
  insufficient_data: "No Data",
};

const sizeClasses = {
  sm: "w-2.5 h-2.5",
  md: "w-3.5 h-3.5",
  lg: "w-5 h-5",
};

export function RagDot({ status, label, size = "md" }: RagDotProps) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div
        className={`${sizeClasses[size]} ${statusColors[status]} rounded-full ring-2 ring-black/30`}
        title={statusLabels[status]}
      />
      <span className="text-xs text-gray-400 text-center leading-tight">
        {label}
      </span>
    </div>
  );
}
