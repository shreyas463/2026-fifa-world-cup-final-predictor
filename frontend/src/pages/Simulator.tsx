import { useState } from "react";
import { api, pct, Simulation, Team } from "../api";
import BracketView from "../components/BracketView";
import { Disclaimer, Flag, Loader, ProbabilityBar, SectionTitle } from "../components/ui";

const PRESETS = [1, 100, 1000, 5000, 10000];

export default function Simulator() {
  const [sims, setSims] = useState(1000);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [single, setSingle] = useState<Simulation | null>(null);
  const [table, setTable] = useState<Team[] | null>(null);
  const [ran, setRan] = useState(0);

  async function run() {
    setBusy(true);
    setErr(null);
    try {
      const res = await api.simulate(sims);
      if (res.mode === "single") {
        setSingle(res.simulation);
        setTable(null);
      } else {
        setTable(res.results);
        setSingle(res.sample_bracket);
      }
      setRan(sims);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setSingle(null);
    setTable(null);
    setRan(0);
    setErr(null);
  }

  return (
    <div>
      <SectionTitle
        title="Tournament Simulator"
        subtitle="Play out the whole World Cup — once for a single storyline, or thousands of times for probabilities."
      />

      <div className="card p-6">
        <div className="mb-4 flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p}
              onClick={() => setSims(p)}
              className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${
                sims === p ? "bg-pitch-500 text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              {p === 1 ? "Single run" : `${p.toLocaleString()}×`}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-400">
            Simulations:
            <input
              type="number"
              min={1}
              max={20000}
              value={sims}
              onChange={(e) => setSims(Math.max(1, Math.min(20000, Number(e.target.value))))}
              className="input w-32"
            />
          </label>
          <button className="btn-primary" onClick={run} disabled={busy}>
            {busy ? "Simulating…" : "🎲 Run simulation"}
          </button>
          {(single || table) && (
            <button className="btn-ghost" onClick={reset}>
              Reset
            </button>
          )}
        </div>
      </div>

      {err && <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{err}</div>}
      {busy && <Loader label={`Simulating ${sims.toLocaleString()} tournament${sims > 1 ? "s" : ""}…`} />}

      {!busy && table && (
        <div className="mt-6 card p-6">
          <h2 className="mb-1 text-lg font-semibold text-white">
            Title probabilities · {ran.toLocaleString()} simulations
          </h2>
          <p className="mb-4 text-sm text-slate-400">Share of simulations each team lifted the trophy.</p>
          <div className="space-y-3">
            {table.slice(0, 12).map((t, i) => (
              <div key={t.id} className="flex items-center gap-3">
                <div className="w-5 text-right text-sm text-slate-500">{i + 1}</div>
                <div className="text-2xl">
                  <Flag flag={t.flag} />
                </div>
                <div className="w-28 shrink-0 text-sm font-medium text-white">{t.name}</div>
                <div className="flex-1">
                  <ProbabilityBar value={t.probabilities.winner} color={i === 0 ? "#f4c542" : "#12a150"} />
                </div>
                <div className="w-14 text-right text-sm font-bold tabular-nums text-pitch-400">
                  {pct(t.probabilities.winner)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!busy && single && (
        <div className="mt-6 space-y-6">
          <div className="card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">
                {table ? "Sample tournament bracket" : "Simulated bracket"}
              </h2>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-slate-400">Winner:</span>
                <span className="text-2xl">{single.champion.flag}</span>
                <span className="font-bold text-gold">{single.champion.name} 🏆</span>
              </div>
            </div>
            <BracketView rounds={single.knockout} champion={single.champion} />
          </div>

          <div className="card p-6">
            <h2 className="mb-4 text-lg font-semibold text-white">Group stage results</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Object.entries(single.groups).map(([g, rows]) => (
                <div key={g} className="rounded-xl border border-white/5 bg-night-900 p-3">
                  <div className="mb-2 text-sm font-semibold text-slate-300">Group {g}</div>
                  <table className="w-full text-xs">
                    <tbody>
                      {rows.map((r) => (
                        <tr key={r.id} className={r.qualified ? "text-white" : "text-slate-500"}>
                          <td className="py-1">
                            {r.flag} {r.name}
                          </td>
                          <td className="py-1 text-right font-mono">{r.points}</td>
                          <td className="w-8 py-1 text-right font-mono text-slate-500">
                            {r.gd > 0 ? `+${r.gd}` : r.gd}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-500">
              White rows qualified for the knockout stage (top 2 of each group + 8 best third-placed teams).
            </p>
          </div>
        </div>
      )}

      <Disclaimer />
    </div>
  );
}
