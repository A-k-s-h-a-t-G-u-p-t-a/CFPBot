"use client";

import { useState } from "react";
import { IconChevronDown, IconChevronUp, IconAlertCircle } from "@tabler/icons-react";

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
  raw: string; // JSON string stored in Prisma
}

// ── Mini bar chart (no library needed) ─────────────────────────────────────

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
      <div className="space-y-2">
        {spec.data.map((bar, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="w-28 shrink-0 truncate text-right text-xs text-slate-400">
              {bar.label}
            </span>
            <div className="relative flex-1 overflow-hidden rounded-full bg-white/5 h-5">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500"
                style={{ width: `${(bar.value / max) * 100}%` }}
              />
            </div>
            <span className="w-20 shrink-0 text-right text-xs text-slate-300">
              {bar.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
      {(spec.x_label || spec.y_label) && (
        <p className="mt-2 text-right text-[10px] text-slate-500">
          {spec.y_label}
        </p>
      )}
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────────────

export default function AnswerCard({ raw }: Props) {
  const [sqlOpen, setSqlOpen] = useState(false);

  let answer: FastAPIAnswer;
  try {
    answer = JSON.parse(raw) as FastAPIAnswer;
  } catch {
    return (
      <p className="text-sm text-red-400">Could not parse response.</p>
    );
  }

  // ── Error response ──
  if (answer.error_code) {
    return (
      <div className="flex gap-3 rounded-xl border border-red-500/20 bg-red-900/10 p-4">
        <IconAlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
        <div className="space-y-1">
          <p className="text-sm font-medium text-red-300">
            {answer.message ?? "Something went wrong."}
          </p>
          {answer.suggestion && (
            <p className="text-xs text-slate-400">{answer.suggestion}</p>
          )}
          <p className="text-[10px] uppercase tracking-wide text-red-500/60">
            {answer.error_code}
          </p>
        </div>
      </div>
    );
  }

  const narrative = answer.answer ?? "No insights returned.";

  return (
    <div className="space-y-3">
      {/* Narrative */}
      <p className="text-sm leading-relaxed text-slate-200">{narrative}</p>

      {/* Anomalies */}
      {answer.anomaly_flag && (
        <div className="rounded-lg border border-yellow-500/20 bg-yellow-900/10 px-3 py-2">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-yellow-400">
            Anomalies
          </p>
          <ul className="space-y-1">
            <li className="text-xs text-slate-300">
              • {answer.anomaly_flag}
            </li>
          </ul>
        </div>
      )}

      {/* Follow Up */}
      {answer.follow_up && (
        <p className="mt-2 text-xs text-slate-400 italic">
          ↳ {answer.follow_up}
        </p>
      )}

      {/* Chart */}
      {answer.chart_data && <MiniBarChart spec={answer.chart_data} />}

      {/* SQL source (collapsible) */}
      {answer.sql_executed && (
        <div className="rounded-xl border border-white/10 bg-[#030915]/60">
          <button
            onClick={() => setSqlOpen((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-2 text-xs text-slate-400 hover:text-slate-200"
          >
            <span>SQL source</span>
            {sqlOpen ? (
              <IconChevronUp className="h-3 w-3" />
            ) : (
              <IconChevronDown className="h-3 w-3" />
            )}
          </button>
          {sqlOpen && (
            <pre className="overflow-x-auto px-4 pb-4 text-[11px] text-cyan-300">
              {answer.sql_executed}
            </pre>
          )}
        </div>
      )}

      {/* Timing */}
      {answer.execution_ms !== undefined && (
        <p className="text-right text-[10px] text-slate-500">
          {answer.execution_ms} ms
        </p>
      )}
    </div>
  );
}
