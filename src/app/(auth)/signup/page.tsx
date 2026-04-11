'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { signIn } from 'next-auth/react';
import Link from 'next/link';
import { FcGoogle } from 'react-icons/fc';
import { FaFacebook } from 'react-icons/fa';
import { IconAdjustmentsBolt, IconChartBar, IconMessageCircleSearch, IconSparkles } from '@tabler/icons-react';

export default function SignUpPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
        headers: { 'Content-Type': 'application/json' },
      });

      if (res.ok) {
        const loginResult = await signIn('credentials', {
          redirect: false,
          email,
          password,
        });

        if (loginResult?.error) {
          router.push('/signin');
        } else {
          router.push('/chat');
        }
      } else {
        const data = await res.json();
        setError(data.message || 'Something went wrong');
      }
    } catch {
      setError('Failed to register');
    }

    setLoading(false);
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#020816] px-4 py-30 text-white md:px-8">
      <div className="pointer-events-none absolute -left-40 top-16 h-96 w-96 rounded-full bg-cyan-500/25 blur-3xl" />
      <div className="pointer-events-none absolute left-1/3 top-1/2 h-80 w-80 rounded-full bg-indigo-500/20 blur-3xl" />
      <div className="pointer-events-none absolute right-0 top-10 h-112 w-md rounded-full bg-blue-600/20 blur-3xl" />

      <div className="relative mx-auto grid w-full max-w-6xl items-center gap-8 md:grid-cols-2">
        <section className="rounded-2xl border border-white/10 bg-white/2 p-6 backdrop-blur-sm md:p-10">
          <p className="mb-8 text-sm font-semibold text-cyan-300">MetricLens</p>
          <div className="space-y-6 text-sm text-slate-300">
            <div className="flex gap-3">
              <IconMessageCircleSearch className="mt-0.5 h-4 w-4 text-cyan-300" />
              <p>Understand what changed in revenue, churn, support, and growth metrics.</p>
            </div>
            <div className="flex gap-3">
              <IconAdjustmentsBolt className="mt-0.5 h-4 w-4 text-cyan-300" />
              <p>Break down totals into categories and identify the biggest contributors.</p>
            </div>
            <div className="flex gap-3">
              <IconChartBar className="mt-0.5 h-4 w-4 text-cyan-300" />
              <p>Compare periods, regions, and products with clear, consistent insights.</p>
            </div>
            <div className="flex gap-3">
              <IconSparkles className="mt-0.5 h-4 w-4 text-cyan-300" />
              <p>Generate weekly and monthly summaries tailored for leadership updates.</p>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-[#050c1f]/80 p-6 shadow-2xl backdrop-blur-sm md:p-8">
          <h1 className="mb-1 text-3xl font-bold">Create account</h1>
          <p className="mb-6 text-sm text-slate-400">Start using MetricLens in minutes.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && <p className="text-sm text-red-400">{error}</p>}

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

            <div>
              <label className="mb-1 block text-xs text-slate-300">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-md border border-white/10 bg-[#030915] px-3 py-2 text-sm text-white outline-none transition focus:border-cyan-400"
              />
            </div>

            <button
              type="submit"
              className="flex w-full items-center justify-center gap-2 rounded-md bg-slate-100 py-2 text-sm font-semibold text-slate-900 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
              disabled={loading}
            >
              {loading && <span className="h-3.5 w-3.5 rounded-full border-2 border-slate-500 border-t-transparent animate-spin" />}
              {loading ? 'Creating account...' : 'Sign up'}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link href="/signin" className="font-medium text-cyan-300 hover:text-cyan-200">
              Sign in
            </Link>
          </p>

          <div className="my-4 flex items-center gap-3 text-xs text-slate-500">
            <div className="h-px flex-1 bg-white/10" />
            <span>or</span>
            <div className="h-px flex-1 bg-white/10" />
          </div>

          <div className="space-y-2">
          </div>
        </section>
      </div>
    </main>
  );
}
