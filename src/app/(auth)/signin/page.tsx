'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { FcGoogle } from 'react-icons/fc';
import { FaFacebook } from 'react-icons/fa';
import {
  IconAdjustmentsBolt,
  IconChartBar,
  IconMessageCircleSearch,
  IconSparkles,
} from '@tabler/icons-react';

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const res = await signIn('credentials', {
      redirect: false,
      email,
      password,
    });

    if (res?.error) {
      setError('Invalid credentials');
    } else {
      router.push('/chat');
    }

    setLoading(false);
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#020816] px-4 py-20 text-white md:px-8">
      {/* Background blobs */}
      <div className="pointer-events-none absolute -left-40 top-16 h-96 w-96 rounded-full bg-cyan-500/25 blur-3xl" />
      <div className="pointer-events-none absolute left-1/3 top-1/2 h-80 w-80 rounded-full bg-indigo-500/20 blur-3xl" />
      <div className="pointer-events-none absolute right-0 top-10 h-112 w-md rounded-full bg-blue-600/20 blur-3xl" />

      <div className="relative mx-auto grid w-full max-w-5xl items-center gap-6 md:grid-cols-2">

        {/* Left panel — feature list */}
        <section className="rounded-2xl border border-white/10 bg-white/2 p-8 backdrop-blur-sm md:p-10">
          {/* Brand */}
          <div className="mb-8 flex items-center gap-2">
            <svg
              className="h-4 w-4 text-cyan-400"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path d="M10 2L3 7v6l7 5 7-5V7L10 2z" />
              <path d="M10 7v6M7 8.5l3-1.5 3 1.5" />
            </svg>
            <span className="text-sm font-semibold text-cyan-300">MetricLens</span>
          </div>

          {/* Features */}
          <div className="space-y-6 text-sm text-slate-300">
            <div className="flex gap-3">
              <IconMessageCircleSearch className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" />
              <p>Ask why metrics changed and get clear, data-backed explanations.</p>
            </div>
            <div className="flex gap-3">
              <IconAdjustmentsBolt className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" />
              <p>Break down drivers by region, product, channel, or team in seconds.</p>
            </div>
            <div className="flex gap-3">
              <IconChartBar className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" />
              <p>Compare periods and segments with consistent metric definitions.</p>
            </div>
            <div className="flex gap-3">
              <IconSparkles className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" />
              <p>Generate concise weekly and monthly summaries leaders can trust.</p>
            </div>
          </div>
        </section>

        {/* Right panel — sign-in form */}
        <section className="rounded-2xl border border-white/10 bg-[#050c1f]/80 p-6 shadow-2xl backdrop-blur-sm md:p-8">
          <h1 className="mb-1 text-3xl font-bold">Sign in</h1>
          <p className="mb-6 text-sm text-slate-400">Welcome back to MetricLens.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <p className="text-sm text-red-400">Invalid credentials</p>
            )}

            {/* Email */}
            <div>
              <label className="mb-1 block text-xs text-slate-300">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@email.com"
                className="w-full rounded-md border border-white/10 bg-[#030915] px-3 py-2 text-sm text-white outline-none transition focus:border-cyan-400"
              />
            </div>

            {/* Password */}
            <div>
              <div className="mb-1 flex items-center justify-between">
                <label className="block text-xs text-slate-300">Password</label>
                <Link
                  href="#"
                  className="text-xs text-cyan-300 hover:text-cyan-200"
                >
                  Forgot your password?
                </Link>
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-md border border-white/10 bg-[#030915] px-3 py-2 text-sm text-white outline-none transition focus:border-cyan-400"
              />
            </div>

            {/* Remember me */}
            <label className="flex cursor-pointer items-center gap-2 text-xs text-slate-300">
              <input
                type="checkbox"
                className="h-3.5 w-3.5 rounded border-white/30 bg-transparent accent-cyan-400"
              />
              Remember me
            </label>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-slate-100 py-2 text-sm font-semibold text-slate-900 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading && <span className="h-3.5 w-3.5 rounded-full border-2 border-slate-500 border-t-transparent animate-spin" />}
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          {/* Sign up link */}
          <p className="mt-4 text-center text-sm text-slate-400">
            Don&apos;t have an account?{' '}
            <Link
              href="/signup"
              className="font-medium text-cyan-300 hover:text-cyan-200"
            >
              Sign up
            </Link>
          </p>

          {/* Divider */}
          <div className="my-4 flex items-center gap-3 text-xs text-slate-500">
            <div className="h-px flex-1 bg-white/10" />
            <span>or</span>
            <div className="h-px flex-1 bg-white/10" />
          </div>

          {/* Social buttons */}
          <div className="space-y-2">
            
          </div>
        </section>

      </div>
    </main>
  );
}