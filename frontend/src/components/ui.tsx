import { ReactNode } from "react";

export function Loader({ label = "Crunching the numbers…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-slate-400">
      <div className="relative h-12 w-12">
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-white/10 border-t-pitch-400" />
        <div className="absolute inset-0 flex items-center justify-center text-lg">⚽</div>
      </div>
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function ErrorMessage({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const isStatic = import.meta.env.VITE_STATIC === "true";
  return (
    <div className="card mx-auto my-10 max-w-lg p-6 text-center">
      <div className="mb-2 text-3xl">⚠️</div>
      <h3 className="mb-1 text-lg font-semibold text-red-300">Couldn't load the data</h3>
      <p className="mb-4 text-sm text-slate-400">{message}</p>
      {!isStatic && (
        <p className="mb-4 text-xs text-slate-500">
          Make sure the prediction API is running at <code>http://localhost:8000</code>.
        </p>
      )}
      {onRetry && (
        <button className="btn-primary" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function Disclaimer({ text }: { text?: string }) {
  return (
    <div className="mt-10 flex items-start gap-3 rounded-xl border border-gold/20 bg-gold/5 p-4 text-xs text-amber-200/80">
      <span className="text-base">ℹ️</span>
      <p>
        {text ??
          "All figures are probability-based statistical estimates, not guaranteed outcomes. Real results are affected by injuries, squad changes, tactics, red cards, penalties and other unpredictable events."}
      </p>
    </div>
  );
}

export function ProbabilityBar({
  value,
  color = "#12a150",
  label,
}: {
  value: number;
  color?: string;
  label?: string;
}) {
  const w = Math.max(0, Math.min(100, value * 100));
  return (
    <div className="w-full">
      {label && (
        <div className="mb-1 flex justify-between text-xs text-slate-400">
          <span>{label}</span>
          <span className="tabular-nums">{w.toFixed(1)}%</span>
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full transition-all" style={{ width: `${w}%`, background: color }} />
      </div>
    </div>
  );
}

export function StatCard({
  label,
  value,
  sub,
  accent = false,
}: {
  label: string;
  value: ReactNode;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div className={`card p-4 ${accent ? "ring-1 ring-pitch-400/40 bg-pitch-500/[0.04]" : ""}`}>
      <div className="eyebrow">{label}</div>
      <div className={`mt-1.5 text-2xl font-bold leading-tight ${accent ? "text-pitch-400" : "text-slate-100"}`}>
        {value}
      </div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

export function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2.5">
        <span className="h-6 w-1 rounded-full bg-pitch-500" />
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-[1.75rem]">{title}</h1>
      </div>
      {subtitle && <p className="mt-1.5 pl-3.5 text-sm text-slate-400">{subtitle}</p>}
    </div>
  );
}

export function Flag({ flag, className = "" }: { flag: string; className?: string }) {
  return <span className={`select-none ${className}`}>{flag}</span>;
}
