"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register } from "@/lib/api";
import { setToken, getToken } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirmPassword: "",
    weight_kg: "",
    height_cm: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (getToken()) {
      router.replace("/");
    }
  }, [router]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
        ...(form.weight_kg ? { weight_kg: parseFloat(form.weight_kg) } : {}),
        ...(form.height_cm ? { height_cm: parseFloat(form.height_cm) } : {}),
      };
      const res = await register(payload);
      setToken(res.access_token);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <span className="text-xl font-black text-white">O</span>
        </div>
        <h1 className="text-2xl font-bold">Create account</h1>
        <p className="text-gray-500 text-sm mt-1">Start your health journey</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        <InputField
          label="Full Name"
          name="full_name"
          type="text"
          value={form.full_name}
          onChange={handleChange}
          placeholder="Jane Smith"
          required
          autoComplete="name"
        />

        <InputField
          label="Email"
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          placeholder="you@example.com"
          required
          autoComplete="email"
        />

        <InputField
          label="Password"
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          placeholder="At least 8 characters"
          required
          autoComplete="new-password"
        />

        <InputField
          label="Confirm Password"
          name="confirmPassword"
          type="password"
          value={form.confirmPassword}
          onChange={handleChange}
          placeholder="Repeat password"
          required
          autoComplete="new-password"
        />

        <div className="pt-2">
          <p className="text-xs text-gray-500 mb-3 uppercase tracking-wider">
            Optional — helps personalise your plan
          </p>
          <div className="grid grid-cols-2 gap-3">
            <InputField
              label="Weight (kg)"
              name="weight_kg"
              type="number"
              value={form.weight_kg}
              onChange={handleChange}
              placeholder="75"
              min="20"
              max="300"
            />
            <InputField
              label="Height (cm)"
              name="height_cm"
              type="number"
              value={form.height_cm}
              onChange={handleChange}
              placeholder="175"
              min="100"
              max="250"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white font-semibold py-3 rounded-xl transition-colors mt-2 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Creating account…
            </>
          ) : (
            "Create Account"
          )}
        </button>
      </form>

      <p className="text-center text-gray-500 text-sm mt-6">
        Already have an account?{" "}
        <Link href="/login" className="text-blue-400 font-medium">
          Sign in
        </Link>
      </p>
    </div>
  );
}

interface InputFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  name: string;
}

function InputField({ label, ...props }: InputFieldProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm text-gray-400" htmlFor={props.name}>
        {label}
      </label>
      <input
        id={props.name}
        {...props}
        className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors text-sm"
      />
    </div>
  );
}
