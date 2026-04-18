"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, logout } from "@/lib/auth";
import { getProfile, updateProfile } from "@/lib/api";
import type { Profile } from "@/lib/api";

function FieldRow({
  label,
  name,
  value,
  type,
  editing,
  onChange,
  placeholder,
  min,
  max,
  options,
}: {
  label: string;
  name: string;
  value: string;
  type?: string;
  editing: boolean;
  onChange: (name: string, value: string) => void;
  placeholder?: string;
  min?: string;
  max?: string;
  options?: Array<{ value: string; label: string }>;
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-800/50 last:border-0">
      <span className="text-sm text-gray-500 w-1/3 flex-shrink-0">{label}</span>
      {editing ? (
        options ? (
          <select
            value={value}
            onChange={(e) => onChange(name, e.target.value)}
            className="flex-1 bg-[#222] border border-gray-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="">Not set</option>
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            type={type ?? "text"}
            value={value}
            onChange={(e) => onChange(name, e.target.value)}
            placeholder={placeholder}
            min={min}
            max={max}
            className="flex-1 bg-[#222] border border-gray-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-blue-500"
          />
        )
      ) : (
        <span className="text-sm text-gray-200 text-right">
          {value
            ? options
              ? (options.find((o) => o.value === value)?.label ?? value)
              : value
            : <span className="text-gray-600">Not set</span>}
        </span>
      )}
    </div>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [form, setForm] = useState({
    full_name: "",
    weight_kg: "",
    height_cm: "",
    date_of_birth: "",
    sex: "",
    protein_target_g: "",
    fibre_target_g: "",
  });

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    getProfile()
      .then((p) => {
        setProfile(p);
        setForm({
          full_name: p.full_name ?? "",
          weight_kg: p.weight_kg?.toString() ?? "",
          height_cm: p.height_cm?.toString() ?? "",
          date_of_birth: p.date_of_birth ?? "",
          sex: p.sex ?? "",
          protein_target_g: p.protein_target_g?.toString() ?? "",
          fibre_target_g: p.fibre_target_g?.toString() ?? "",
        });
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load profile.")
      )
      .finally(() => setLoading(false));
  }, [router]);

  function handleChange(name: string, value: string) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const payload: Partial<Profile> = {
        full_name: form.full_name.trim() || undefined,
        weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : undefined,
        height_cm: form.height_cm ? parseFloat(form.height_cm) : undefined,
        date_of_birth: form.date_of_birth || undefined,
        sex: form.sex || undefined,
        protein_target_g: form.protein_target_g
          ? parseFloat(form.protein_target_g)
          : undefined,
        fibre_target_g: form.fibre_target_g
          ? parseFloat(form.fibre_target_g)
          : undefined,
      };

      const updated = await updateProfile(payload);
      setProfile(updated);
      setEditing(false);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    if (profile) {
      setForm({
        full_name: profile.full_name ?? "",
        weight_kg: profile.weight_kg?.toString() ?? "",
        height_cm: profile.height_cm?.toString() ?? "",
        date_of_birth: profile.date_of_birth ?? "",
        sex: profile.sex ?? "",
        protein_target_g: profile.protein_target_g?.toString() ?? "",
        fibre_target_g: profile.fibre_target_g?.toString() ?? "",
      });
    }
    setEditing(false);
    setError(null);
  }

  // Compute BMI
  const bmi =
    form.weight_kg && form.height_cm
      ? (
          parseFloat(form.weight_kg) /
          Math.pow(parseFloat(form.height_cm) / 100, 2)
        ).toFixed(1)
      : null;

  return (
    <div className="flex flex-col min-h-screen px-4 pt-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Profile</h1>
        {!editing ? (
          <button
            onClick={() => setEditing(true)}
            className="text-sm text-blue-400 font-medium"
          >
            Edit
          </button>
        ) : (
          <div className="flex gap-3">
            <button
              onClick={handleCancel}
              className="text-sm text-gray-500"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="text-sm text-blue-400 font-medium"
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        )}
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

      {success && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 mb-4">
          <p className="text-green-400 text-sm">Profile saved successfully.</p>
        </div>
      )}

      {!loading && profile && (
        <div className="space-y-4">
          {/* Avatar / Email */}
          <div className="flex flex-col items-center py-4">
            <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mb-3">
              <span className="text-3xl font-bold text-white">
                {profile.full_name?.charAt(0)?.toUpperCase() ?? "?"}
              </span>
            </div>
            <p className="text-sm text-gray-500">{profile.email}</p>
            {bmi && (
              <div className="mt-2 px-3 py-1 bg-gray-800 rounded-full">
                <span className="text-xs text-gray-400">BMI: </span>
                <span className="text-xs font-medium text-white">{bmi}</span>
              </div>
            )}
          </div>

          {/* Personal Info */}
          <div className="bg-[#111111] rounded-2xl px-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider pt-4 pb-2">
              Personal
            </h2>
            <FieldRow
              label="Name"
              name="full_name"
              value={form.full_name}
              editing={editing}
              onChange={handleChange}
              placeholder="Full name"
            />
            <FieldRow
              label="Date of Birth"
              name="date_of_birth"
              value={form.date_of_birth}
              type="date"
              editing={editing}
              onChange={handleChange}
            />
            <FieldRow
              label="Sex"
              name="sex"
              value={form.sex}
              editing={editing}
              onChange={handleChange}
              options={[
                { value: "male", label: "Male" },
                { value: "female", label: "Female" },
                { value: "other", label: "Other" },
              ]}
            />
          </div>

          {/* Biometrics */}
          <div className="bg-[#111111] rounded-2xl px-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider pt-4 pb-2">
              Biometrics
            </h2>
            <FieldRow
              label="Weight"
              name="weight_kg"
              value={form.weight_kg}
              type="number"
              editing={editing}
              onChange={handleChange}
              placeholder="kg"
              min="20"
              max="300"
            />
            <FieldRow
              label="Height"
              name="height_cm"
              value={form.height_cm}
              type="number"
              editing={editing}
              onChange={handleChange}
              placeholder="cm"
              min="100"
              max="250"
            />
          </div>

          {/* Nutrition Targets */}
          <div className="bg-[#111111] rounded-2xl px-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider pt-4 pb-2">
              Nutrition Targets
            </h2>
            <FieldRow
              label="Protein"
              name="protein_target_g"
              value={form.protein_target_g}
              type="number"
              editing={editing}
              onChange={handleChange}
              placeholder="g/day"
              min="0"
              max="500"
            />
            <FieldRow
              label="Fibre"
              name="fibre_target_g"
              value={form.fibre_target_g}
              type="number"
              editing={editing}
              onChange={handleChange}
              placeholder="g/day"
              min="0"
              max="100"
            />
          </div>

          {/* Navigation links */}
          <div className="bg-[#111111] rounded-2xl divide-y divide-gray-800/50">
            {[
              { label: "Goals", href: "/goals" },
              { label: "Wearables", href: "/wearables" },
              { label: "Lab Results", href: "/labs" },
            ].map((item) => (
              <button
                key={item.href}
                onClick={() => router.push(item.href)}
                className="w-full flex items-center justify-between px-4 py-3 text-sm text-gray-300 hover:bg-white/5 transition-colors"
              >
                {item.label}
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-gray-600">
                  <path fillRule="evenodd" d="M16.28 11.47a.75.75 0 0 1 0 1.06l-7.5 7.5a.75.75 0 0 1-1.06-1.06L14.69 12 7.72 5.03a.75.75 0 0 1 1.06-1.06l7.5 7.5Z" clipRule="evenodd" />
                </svg>
              </button>
            ))}
          </div>

          {/* Logout */}
          <button
            onClick={logout}
            className="w-full bg-red-500/10 border border-red-500/20 text-red-400 font-medium py-3 rounded-2xl text-sm hover:bg-red-500/20 transition-colors"
          >
            Sign Out
          </button>

          <div className="pb-4" />
        </div>
      )}
    </div>
  );
}
