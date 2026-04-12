import { Timeline } from "@/src/components/ui/timeline";

/* ── Understand: chat interface mockup ─────────────────────────── */
const ChatMockup = () => (
  <div className="rounded-xl border border-neutral-800 bg-neutral-950 overflow-hidden text-xs font-sans">
    <div className="flex items-center gap-2 px-4 py-2.5 border-b border-neutral-800 bg-neutral-900/60">
      <div className="flex gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full bg-neutral-700" />
        <span className="w-2.5 h-2.5 rounded-full bg-neutral-700" />
        <span className="w-2.5 h-2.5 rounded-full bg-neutral-700" />
      </div>
      <span className="text-neutral-500 text-xs ml-1 font-mono">MetricLens</span>
    </div>
    <div className="p-4 space-y-3">
      <div className="flex justify-end">
        <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-3.5 py-2 text-xs max-w-[80%] leading-relaxed">
          Why did customer complaints rise in September?
        </div>
      </div>
      <div className="bg-neutral-900 rounded-2xl rounded-tl-sm p-4 text-xs space-y-2.5">
        <p className="text-neutral-100 font-semibold leading-relaxed">
          Complaint volume rose 34% in September, driven by three factors:
        </p>
        <div className="space-y-1.5">
          <div className="flex items-start gap-2 text-neutral-300">
            <span className="text-red-400 font-bold font-mono shrink-0">↑58%</span>
            <span>Billing errors following system updates Sept 3–7</span>
          </div>
          <div className="flex items-start gap-2 text-neutral-300">
            <span className="text-red-400 font-bold font-mono shrink-0">↑41%</span>
            <span>App downtime incident, Sept 12–14</span>
          </div>
          <div className="flex items-start gap-2 text-neutral-300">
            <span className="text-orange-400 font-bold font-mono shrink-0">↑27%</span>
            <span>Onboarding delays, East region</span>
          </div>
        </div>
        <div className="pt-2 flex items-center gap-1.5 border-t border-neutral-800">
          <span className="text-blue-500">◈</span>
          <span className="text-neutral-600">Sources: CRM Export · Ops Report · App Logs</span>
        </div>
      </div>
    </div>
  </div>
);

const InsightCard = () => (
  <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 space-y-4 h-full">
    <div className="flex items-center justify-between">
      <span className="text-neutral-500 text-xs font-medium uppercase tracking-widest">
        Net Promoter Score
      </span>
      <span className="text-xs text-red-400 bg-red-400/10 rounded-full px-2 py-0.5">
        ↓ 8 pts
      </span>
    </div>
    <div className="text-5xl font-bold text-white font-mono">63</div>
    <div className="h-px bg-neutral-800" />
    <p className="text-xs text-neutral-500 leading-relaxed">
      Biggest driver: detractor scores in billing and app stability categories.
    </p>
    <div className="flex items-center gap-2 pt-1">
      <span className="text-xs text-blue-500">◈</span>
      <span className="text-xs text-neutral-600">Source: NPS Survey, Sept 2024</span>
    </div>
  </div>
);

/* ── Breakdown: horizontal bar chart mockup ─────────────────────── */
const BreakdownMockup = () => (
  <div className="col-span-2 rounded-xl border border-neutral-800 bg-neutral-950 overflow-hidden text-xs">
    <div className="px-5 py-3.5 border-b border-neutral-800 flex items-center justify-between">
      <span className="text-neutral-100 font-semibold text-sm">
        Revenue Breakdown — Q3 2024
      </span>
      <span className="text-neutral-500 font-mono">Total: £9.3M</span>
    </div>
    <div className="p-5 space-y-4">
      {[
        { label: "North Region", value: "£4.2M", pct: 45, trend: "+12%", up: true,  color: "bg-blue-500" },
        { label: "South Region", value: "£2.1M", pct: 23, trend: "+4%",  up: true,  color: "bg-blue-400" },
        { label: "East Region",  value: "£1.8M", pct: 19, trend: "−3%",  up: false, color: "bg-indigo-400" },
        { label: "West Region",  value: "£1.2M", pct: 13, trend: "+7%",  up: true,  color: "bg-indigo-500" },
      ].map(({ label, value, pct, trend, up, color }) => (
        <div key={label} className="space-y-1.5">
          <div className="flex justify-between items-center text-neutral-300">
            <span>{label}</span>
            <div className="flex items-center gap-3">
              <span className={`text-xs ${up ? "text-green-400" : "text-red-400"}`}>
                {trend} QoQ
              </span>
              <span className="font-mono text-neutral-100 w-14 text-right">{value}</span>
              <span className="text-neutral-600 w-7 text-right">{pct}%</span>
            </div>
          </div>
          <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
            <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
          </div>
        </div>
      ))}
    </div>
  </div>
);

/* ── Compare: side-by-side table mockup ─────────────────────────── */
const CompareMockup = () => (
  <div className="col-span-2 rounded-xl border border-neutral-800 bg-neutral-950 overflow-hidden text-xs">
    <div className="px-5 py-3.5 border-b border-neutral-800 flex items-center gap-3">
      <span className="text-neutral-100 font-semibold text-sm">
        Week-on-Week Comparison
      </span>
      <span className="text-neutral-700">·</span>
      <span className="text-neutral-500">W42 vs W41, 2024</span>
    </div>
    <table className="w-full">
      <thead>
        <tr className="border-b border-neutral-800">
          <th className="text-left px-5 py-2.5 text-neutral-500 font-medium">Metric</th>
          <th className="text-right px-4 py-2.5 text-neutral-500 font-medium">W42</th>
          <th className="text-right px-4 py-2.5 text-neutral-500 font-medium">W41</th>
          <th className="text-right px-5 py-2.5 text-neutral-500 font-medium">Change</th>
        </tr>
      </thead>
      <tbody className="text-neutral-300">
        {[
          { metric: "Revenue",      current: "£2.4M", prev: "£2.1M", change: "+14.3%", up: true  },
          { metric: "Churn Rate",   current: "2.3%",  prev: "1.9%",  change: "+0.4pp", up: false },
          { metric: "NPS Score",    current: "67",    prev: "71",    change: "−4 pts",  up: false },
          { metric: "Open Tickets", current: "143",   prev: "189",   change: "−24.3%", up: true  },
        ].map(({ metric, current, prev, change, up }, i) => (
          <tr key={metric} className={i < 3 ? "border-b border-neutral-800/50" : ""}>
            <td className="px-5 py-3">{metric}</td>
            <td className="px-4 py-3 text-right font-mono text-neutral-100">{current}</td>
            <td className="px-4 py-3 text-right font-mono text-neutral-500">{prev}</td>
            <td className={`px-5 py-3 text-right font-mono font-semibold ${up ? "text-green-400" : "text-red-400"}`}>
              {change}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

/* ── Export ──────────────────────────────────────────────────────── */
export function TimelineDemo() {
  const data = [
    {
      title: "Understand",
      content: (
        <div>
          <p className="mb-6 text-sm font-normal text-neutral-800 md:text-lg dark:text-white max-w-2xl leading-relaxed">
            MetricLens explains why revenue dropped, why complaints rose, or
            what changed in any metric. It identifies the biggest drivers and
            references the source data behind every insight.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <ChatMockup />
            <InsightCard />
          </div>
        </div>
      ),
    },
    {
      title: "Breakdown",
      content: (
        <div>
          <p className="mb-6 text-sm font-normal text-neutral-800 md:text-lg dark:text-white max-w-2xl leading-relaxed">
            Break totals into region, product, channel, or department
            components. MetricLens surfaces concentration, outliers, and the
            largest contributors automatically.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <BreakdownMockup />
          </div>
        </div>
      ),
    },
    {
      title: "Compare",
      content: (
        <div>
          <p className="mb-6 text-sm font-normal text-neutral-800 md:text-lg dark:text-white max-w-2xl leading-relaxed">
            Compare this week vs last week, region A vs region B, or product
            X vs product Y. MetricLens keeps metric definitions consistent and
            calls out statistically relevant differences.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <CompareMockup />
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="relative w-full overflow-clip">
      <Timeline data={data} />
    </div>
  );
}
