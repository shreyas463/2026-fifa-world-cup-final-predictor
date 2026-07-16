import { useState } from "react";
import { api, MatchPrediction, pct } from "../api";
import { useAsync } from "../hooks";
import { Disclaimer, ErrorMessage, Flag, Loader, SectionTitle } from "../components/ui";

export default function MatchPredictor() {
  const teamsQ = useAsync(() => api.teams(), []);
  const [a, setA] = useState<number>(1);
  const [b, setB] = useState<number>(2);
  const [neutral, setNeutral] = useState(true);
  const [result, setResult] = useState<MatchPrediction | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    if (a === b) {
      setErr("Please choose two different teams.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      const res = await api.predictMatch(a, b, neutral);
      setResult(res.prediction);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (teamsQ.loading) return <Loader />;
  if (teamsQ.error) return <ErrorMessage message={teamsQ.error} onRetry={teamsQ.reload} />;
  const teams = teamsQ.data!.teams;

  const Select = ({ value, onChange, label }: { value: number; onChange: (v: number) => void; label: string }) => (
    <select className="input" value={value} onChange={(e) => onChange(Number(e.target.value))} aria-label={label}>
      {teams.map((t) => (
        <option key={t.id} value={t.id}>
          {t.flag} {t.name}
        </option>
      ))}
    </select>
  );

  return (
    <div>
      <SectionTitle title="Match Predictor" subtitle="Pick any two teams and generate a full match prediction." />

      <div className="card grid items-end gap-4 p-6 md:grid-cols-[1fr_auto_1fr_auto]">
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wide text-slate-400">Team A</label>
          <Select value={a} onChange={setA} label="Select team A" />
        </div>
        <div className="pb-2.5 text-center text-lg font-bold text-slate-500">vs</div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wide text-slate-400">Team B</label>
          <Select value={b} onChange={setB} label="Select team B" />
        </div>
        <button className="btn-primary h-[46px]" onClick={run} disabled={busy}>
          {busy ? "Predicting…" : "Predict Match"}
        </button>
      </div>

      <label className="mt-3 flex items-center gap-2 text-sm text-slate-400">
        <input type="checkbox" checked={neutral} onChange={(e) => setNeutral(e.target.checked)} className="accent-pitch-500" />
        Neutral venue (uncheck to apply host advantage)
      </label>

      {err && <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{err}</div>}
      {busy && <Loader label="Running the model…" />}

      {result && !busy && <MatchResult r={result} />}

      <Disclaimer />
    </div>
  );
}

function MatchResult({ r }: { r: MatchPrediction }) {
  const p = r.probabilities;
  const bars = [
    { label: r.team_a.name, value: p.team_a_win, color: "#12a150" },
    { label: "Draw", value: p.draw, color: "#64748b" },
    { label: r.team_b.name, value: p.team_b_win, color: "#3b82f6" },
  ];
  return (
    <div className="mt-6 space-y-6">
      <div className="card p-6">
        <div className="mb-6 flex items-center justify-between">
          <TeamHead flag={r.team_a.flag} name={r.team_a.name} rank={r.ranking_comparison.team_a} />
          <div className="text-center">
            <div className="text-xs uppercase tracking-wide text-slate-400">Predicted score</div>
            <div className="text-4xl font-extrabold text-white">
              {r.predicted_score.team_a} – {r.predicted_score.team_b}
            </div>
            <div className="text-xs text-slate-500">
              xG {r.expected_goals.team_a} – {r.expected_goals.team_b}
            </div>
          </div>
          <TeamHead flag={r.team_b.flag} name={r.team_b.name} rank={r.ranking_comparison.team_b} right />
        </div>

        <div className="flex h-9 w-full overflow-hidden rounded-full text-xs font-semibold">
          {bars.map((s) => (
            <div
              key={s.label}
              className="flex items-center justify-center text-white"
              style={{ width: `${s.value * 100}%`, background: s.color }}
              title={`${s.label}: ${pct(s.value)}`}
            >
              {s.value > 0.08 ? pct(s.value) : ""}
            </div>
          ))}
        </div>
        <div className="mt-2 flex justify-between text-xs text-slate-400">
          <span>{r.team_a.name} win</span>
          <span>Draw</span>
          <span>{r.team_b.name} win</span>
        </div>
        <div className="mt-3 text-center text-xs text-slate-500">Model: {r.model}</div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h3 className="mb-3 font-semibold text-white">Key factors</h3>
          <div className="space-y-3">
            {r.key_factors.map((f) => (
              <div key={f.factor} className="rounded-xl bg-white/5 p-3">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-slate-200">{f.factor}</span>
                  <span className="text-pitch-400">{f.favours}</span>
                </div>
                <div className="mt-1 text-xs text-slate-500">{f.detail}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="mb-3 font-semibold text-white">Recent head-to-head</h3>
          <div className="space-y-2">
            {r.head_to_head.map((h, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-sm">
                <span className="text-slate-400">{h.year}</span>
                <span className="font-medium text-slate-200">
                  {h.team_a} <span className="font-bold text-white">{h.score_a} – {h.score_b}</span> {h.team_b}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 text-center text-sm">
            <div className="rounded-lg bg-white/5 p-3">
              <div className="text-xs text-slate-400">Form (A / B)</div>
              <div className="font-semibold text-white">
                {r.form_comparison.team_a} / {r.form_comparison.team_b}
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-3">
              <div className="text-xs text-slate-400">FIFA rank (A / B)</div>
              <div className="font-semibold text-white">
                #{r.ranking_comparison.team_a} / #{r.ranking_comparison.team_b}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TeamHead({ flag, name, rank, right }: { flag: string; name: string; rank: number; right?: boolean }) {
  return (
    <div className={`flex items-center gap-3 ${right ? "flex-row-reverse text-right" : ""}`}>
      <div className="text-5xl">
        <Flag flag={flag} />
      </div>
      <div>
        <div className="font-bold text-white">{name}</div>
        <div className="text-xs text-slate-500">FIFA #{rank}</div>
      </div>
    </div>
  );
}
