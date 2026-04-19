"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { forgotPassword } from "@/lib/api";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { reset_token } = await forgotPassword(email);
      if (reset_token) {
        setResetToken(reset_token);
      } else {
        // Email not found — show same success message to avoid enumeration
        setResetToken("not_found");
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (resetToken) {
    if (resetToken === "not_found") {
      return (
        <div className="flex flex-col justify-center min-h-screen px-6">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-white">
                <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clipRule="evenodd" />
              </svg>
            </div>
            <h1 className="text-xl font-bold mb-2">Check your inbox</h1>
            <p className="text-gray-500 text-sm">If that email is registered, a reset link is on its way.</p>
          </div>
          <Link href="/login" className="text-center text-blue-400 text-sm font-medium">
            Back to Sign In
          </Link>
        </div>
      );
    }

    // Token returned directly (no email service yet) — show copy link
    const resetUrl = `${typeof window !== "undefined" ? window.location.origin : ""}/reset-password?token=${resetToken}`;
    return (
      <div className="flex flex-col justify-center min-h-screen px-6">
        <div className="mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-white">
              <path fillRule="evenodd" d="M15.75 1.5a6.75 6.75 0 0 0-6.651 7.906c.067.39-.032.717-.221.906l-6.5 6.499a3 3 0 0 0-.878 2.121v2.818c0 .414.336.75.75.75H6a.75.75 0 0 0 .75-.75v-1.5h1.5A.75.75 0 0 0 9 19.5V18h1.5a.75.75 0 0 0 .53-.22l2.658-2.658c.19-.189.517-.288.906-.22A6.75 6.75 0 1 0 15.75 1.5Zm0 3a.75.75 0 0 0 0 1.5A2.25 2.25 0 0 1 18 8.25a.75.75 0 0 0 1.5 0 3.75 3.75 0 0 0-3.75-3.75Z" clipRule="evenodd" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-center mb-1">Reset link ready</h1>
          <p className="text-gray-500 text-sm text-center mb-6">Tap the button below to set your new password.</p>
          <button
            onClick={() => router.push(`/reset-password?token=${resetToken}`)}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            Set new password
          </button>
          <p className="text-xs text-gray-600 text-center mt-4">Link expires in 1 hour.</p>
        </div>
        <Link href="/login" className="text-center text-blue-400 text-sm font-medium">
          Back to Sign In
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col justify-center min-h-screen px-6">
      <div className="mb-10 text-center">
        <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl font-black text-white">O</span>
        </div>
        <h1 className="text-2xl font-bold">Forgot password?</h1>
        <p className="text-gray-500 text-sm mt-1">Enter your email and we&apos;ll send a reset link.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        <div className="space-y-2">
          <label className="text-sm text-gray-400" htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            placeholder="you@example.com"
            className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white font-semibold py-3 rounded-xl transition-colors mt-2 flex items-center justify-center gap-2"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : "Send reset link"}
        </button>
      </form>

      <p className="text-center text-gray-500 text-sm mt-6">
        Remember it?{" "}
        <Link href="/login" className="text-blue-400 font-medium">Sign In</Link>
      </p>
    </div>
  );
}
