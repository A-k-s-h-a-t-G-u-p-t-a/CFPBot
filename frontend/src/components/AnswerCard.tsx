"use client";

import { useState } from "react";
import {
  IconChevronDown,
  IconChevronUp,
  IconAlertTriangle,
  IconWifiOff,
  IconRefresh,
} from "@tabler/icons-react";

// ── Types mirroring FastAPI response ───────────────────────────────────────

interface ChartBar {
  label: string;
  value: number;
}

interface ChartSpec {
  type: string;
  title?: string;
  x_label?: string;
  y_label?: string;
  data: ChartBar[];
}

interface FastAPIAnswer {
  // Success path
  answer?: string;
  chart_data?: ChartSpec;
  follow_up?: string;
  anomaly_flag?: string;
  metric_used?: string;
  intent?: string;
  confidence?: number;
  sql_executed?: string;
  execution_ms?: number;
  // Error path
  error_code?: string;
  message?: string;
  suggestion?: string;
  recoverable?: boolean;
}

interface Props {
  raw: string;
}

// ── Mini bar chart ─────────────────────────────────────────────────────────

function MiniBarChart({ spec }: { spec: ChartSpec }) {
  if (!spec.data?.length) return null;

  const max = Math.max(...spec.data.map((d) => d.value), 1);

  return (
    <div className="mt-4 rounded-xl border border-white/10 bg-[#030915]/60 p-4">
      {spec.title && (
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-cyan-400">
          {spec.title}
        </p>
      )}
      <div className="space-y-2.5">
        {spec.data.map((bar, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="w-28 shrink-0 truncate text-right text-xs text-slate-400">
              {bar.label}
            </span>
            <div className="relative flex-1 overflow-hidden rounded-full bg-white/5 h-4">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-700"
                style={{ width: `${(bar.value / max) * 100}%` }}
              />
            </div>
            <span className="w-20 shrink-0 text-right text-xs font-medium text-slate-300">
              {bar.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
      {spec.y_label && (
        <p className="mt-2 text-right text-[10px] text-slate-500">{spec.y_label}</p>
      )}
    </div>
  );
}

// ── Confidence badge ───────────────────────────────────────────────────────

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? "text-emerald-400 bg-emerald-500/10 ring-emerald-500/20" :
    pct >= 50 ? "text-amber-400 bg-amber-500/10 ring-amber-500/20" :
                "text-red-400 bg-red-500/10 ring-red-500/20";

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ${color}`}>
      {pct}% confidence
    </span>
  );
}

// ── Main component ──────────────────────────────────────────────────────────

export default function AnswerCard({ raw }: Props) {
  const [sqlOpen, setSqlOpen] = useState(false);

  let answer: FastAPIAnswer;
  try {
    answer = JSON.parse(raw) as FastAPIAnswer;
  } catch {
    return <p className="text-sm text-red-400">Could not parse response.</p>;
  }

  // ── Error response ──────────────────────────────────────────────────────
  if (answer.error_code) {
    // Simplify verbose "Backend unreachable: FastAPI 500: {...}" messages
    let displayMessage = answer.message ?? "Something went wrong.";
    if (
      displayMessage.startsWith("Backend unreachable:") ||
      displayMessage.includes("FastAPI") ||
      displayMessage.includes("INTERNAL_ERROR")
    ) {
      displayMessage = "The analytics backend is currently unavailable.";
    }

    const isNetworkError = answer.error_code === "LLM_UNAVAILABLE";

    return (
      <div className="flex gap-3 rounded-xl border border-red-500/15 bg-red-950/20 p-4">
        <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-red-500/10 ring-1 ring-red-500/20">
          {isNetworkError ? (
            <IconWifiOff className="h-3.5 w-3.5 text-red-400" />
          ) : (
            <IconAlertTriangle className="h-3.5 w-3.5 text-red-400" />
          )}
        </div>
        <div className="min-w-0 space-y-1.5">
          <p className="text-sm font-medium text-red-300">{displayMessage}</p>
          {answer.suggestion && (
            <p className="flex items-center gap-1.5 text-xs text-slate-400">
              <IconRefresh className="h-3 w-3 shrink-0 text-slate-500" />
              {answer.suggestion}
            </p>
          )}
          <p className="text-[10px] font-mono uppercase tracking-widest text-red-500/50">
            {answer.error_code}
          </p>
        </div>
      </div>
    );
  }

  // ── Success response ────────────────────────────────────────────────────
  const narrative = answer.answer ?? "No insights returned.";

  return (
    <div className="space-y-3">
      {/* Narrative */}
      <p className="text-sm leading-relaxed text-slate-200">{narrative}</p>

      {/* Confidence */}
      {answer.confidence !== undefined && (
        <ConfidenceBadge value={answer.confidence} />
      )}

      {/* Anomalies */}
      {answer.anomaly_flag && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-900/10 px-3 py-2.5">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-amber-400">
            Anomaly Detected
          </p>
          <p className="text-xs text-slate-300">• {answer.anomaly_flag}</p>
        </div>
      )}

      {/* Follow-up suggestion */}
      {answer.follow_up && (
        <p className="text-xs italic text-slate-400">
          ↳ {answer.follow_up}
        </p>
      )}

      {/* Chart */}
      {answer.chart_data && <MiniBarChart spec={answer.chart_data} />}

      {/* SQL source */}
      {answer.sql_executed && (
        <div className="rounded-xl border border-white/8 bg-[#030915]/60 overflow-hidden">
          <button
            onClick={() => setSqlOpen((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-2.5 text-xs text-slate-500 transition-colors hover:text-slate-300"
          >
            <span className="font-medium">View SQL</span>
            {sqlOpen ? (
              <IconChevronUp className="h-3 w-3" />
            ) : (
              <IconChevronDown className="h-3 w-3" />
            )}
          </button>
          {sqlOpen && (
            <pre className="overflow-x-auto border-t border-white/5 px-4 pb-4 pt-3 text-[11px] leading-relaxed text-cyan-300">
              {answer.sql_executed}
            </pre>
          )}
        </div>
      )}

      {/* Timing */}
      {answer.execution_ms !== undefined && (
        <p className="text-right text-[10px] text-slate-600">
          ⚡ {answer.execution_ms} ms
        </p>
      )}
    </div>
  );
}
