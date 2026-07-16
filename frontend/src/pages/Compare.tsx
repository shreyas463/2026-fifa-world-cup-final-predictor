import { useState } from "react";
import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import { api, pct, TeamDetail } from "../api";
import { useAsync } from "../hooks";
import { Disclaimer, ErrorMessage, Flag, Loader, SectionTitle } from "../components/ui";

export default function Compare() {
  const teamsQ = useAsync(() => api.teams(), []);
  const [a, setA] = useState(1);
  const [b, setB] = useState(2);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [data, setData] = useState<Awaited<ReturnType<typeof api.comparison>> | null>(null);

  async function run() {
    if (a === b) {
      setErr("Choose two different teams.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      setData(await api.comparison(a, b));
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (teamsQ.loading) return <Loader />;
  if (teamsQ.error) return <ErrorMessage message={teamsQ.error} onRetry={teamsQ.reload} />;
  const teams = teamsQ.data!.teams;

  return (
    <div>
      <SectionTitle title="Team Comparison" subtitle="Put two nations head-to-head across every key metric." />

      <div className="card grid items-end gap-4 p-6 md:grid-cols-[1fr_auto_1fr_auto]">
        <select className="input" value={a} onChange={(e) => setA(Number(e.target.value))} aria-label="Team A">
          {teams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.flag} {t.name}
            </option>
          ))}
        </select>
        <div className="pb-2.5 text-center font-bold text-slate-500">vs</div>
        <select className="input" value={b} onChange={(e) => setB(Number(e.target.value))} aria-label="Team B">
          {teams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.flag} {t.name}
            </option>
          ))}
        </select>
        <button className="btn-primary h-[46px]" onClick={run} disabled={busy}>
          {busy ? "Comparing…" : "Compare"}
        </button>
      </div>

      {err && <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{err}</div>}
      {busy && <Loader />}

      {data && !busy && <ComparisonView data={data} />}

      <Disclaimer />
    </div>
  );
}

function ComparisonView({ data }: { data: Awaited<ReturnType<typeof api.comparison>> }) {
  const a = data.team_a;
  const b = data.team_b;
  const labels = data.attribute_labels;

  const radarData = Object.keys(labels).map((k) => ({
    attribute: labels[k],
    [a.name]: a.attributes[k],
    [b.name]: b.attributes[k],
  }));

  const rows: { label: string; av: number | string; bv: number | string; aRaw: number; bRaw: number; higher?: "lower" }[] = [
    { label: "Elo rating", av: Math.round(a.elo), bv: Math.round(b.elo), aRaw: a.elo, bRaw: b.elo },
    { label: "FIFA rank (field)", av: `#${a.fifa_rank}`, bv: `#${b.fifa_rank}`, aRaw: -a.fifa_rank, bRaw: -b.fifa_rank },
    { label: "FIFA points", av: Math.round(a.fifa_points), bv: Math.round(b.fifa_points), aRaw: a.fifa_points, bRaw: b.fifa_points },
    { label: "Recent form", av: a.form, bv: b.form, aRaw: a.form, bRaw: b.form },
    { label: "Avg goals scored", av: a.attack, bv: b.attack, aRaw: a.attack, bRaw: b.attack },
    { label: "Avg goals conceded", av: a.defense, bv: b.defense, aRaw: -a.defense, bRaw: -b.defense },
    { label: "Squad value (€M)", av: a.squad_value_m, bv: b.squad_value_m, aRaw: a.squad_value_m, bRaw: b.squad_value_m },
    { label: "Squad availability", av: `${a.availability}%`, bv: `${b.availability}%`, aRaw: a.availability, bRaw: b.availability },
    { label: "Fan sentiment", av: Math.round(a.sentiment), bv: Math.round(b.sentiment), aRaw: a.sentiment, bRaw: b.sentiment },
    { label: "WC appearances", av: a.wc_appearances, bv: b.wc_appearances, aRaw: a.wc_appearances, bRaw: b.wc_appearances },
    { label: "WC titles", av: a.wc_titles, bv: b.wc_titles, aRaw: a.wc_titles, bRaw: b.wc_titles },
    {
      label: "Win World Cup",
      av: pct(a.probabilities.winner),
      bv: pct(b.probabilities.winner),
      aRaw: a.probabilities.winner,
      bRaw: b.probabilities.winner,
    },
  ];

  return (
    <div className="mt-6 space-y-6">
      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="card p-6">
          <div className="mb-4 flex items-center justify-around">
            <TeamHead t={a} />
            <div className="text-2xl font-bold text-slate-600">VS</div>
            <TeamHead t={b} />
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-sm">
            <div className="rounded-lg bg-pitch-500/10 p-3">
              <div className="text-xs text-slate-400">{a.name} win</div>
              <div className="font-bold text-pitch-400">{pct(data.match_preview.team_a_win)}</div>
            </div>
            <div className="rounded-lg bg-white/5 p-3">
              <div className="text-xs text-slate-400">Draw</div>
              <div className="font-bold text-slate-200">{pct(data.match_preview.draw)}</div>
            </div>
            <div className="rounded-lg bg-blue-500/10 p-3">
              <div className="text-xs text-slate-400">{b.name} win</div>
              <div className="font-bold text-blue-400">{pct(data.match_preview.team_b_win)}</div>
            </div>
          </div>
          <p className="mt-2 text-center text-xs text-slate-500">Neutral-venue match preview</p>
        </div>

        <div className="card p-6">
          <h3 className="mb-2 font-semibold text-white">Attribute radar</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData} outerRadius="70%">
              <PolarGrid stroke="rgba(255,255,255,0.12)" />
              <PolarAngleAxis dataKey="attribute" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Radar dataKey={a.name} stroke="#12a150" fill="#12a150" fillOpacity={0.35} />
              <Radar dataKey={b.name} stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/5 text-slate-400">
              <th className="p-3 text-right">
                {a.flag} {a.name}
              </th>
              <th className="p-3 text-center text-xs uppercase tracking-wide">Metric</th>
              <th className="p-3 text-left">
                {b.flag} {b.name}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const aWin = r.aRaw > r.bRaw;
              const bWin = r.bRaw > r.aRaw;
              return (
                <tr key={r.label} className="border-b border-white/5">
                  <td className={`p-3 text-right font-semibold ${aWin ? "text-pitch-400" : "text-slate-300"}`}>
                    {r.av} {aWin && "◀"}
                  </td>
                  <td className="p-3 text-center text-xs text-slate-500">{r.label}</td>
                  <td className={`p-3 text-left font-semibold ${bWin ? "text-blue-400" : "text-slate-300"}`}>
                    {bWin && "▶"} {r.bv}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="card p-6">
        <h3 className="mb-3 font-semibold text-white">Recent head-to-head</h3>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {data.head_to_head.map((h, i) => (
            <div key={i} className="rounded-lg bg-white/5 px-3 py-2 text-sm">
              <span className="text-slate-500">{h.year}: </span>
              <span className="font-medium text-white">
                {h.score_a} – {h.score_b}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function TeamHead({ t }: { t: TeamDetail }) {
  return (
    <div className="text-center">
      <div className="text-5xl">
        <Flag flag={t.flag} />
      </div>
      <div className="mt-1 font-bold text-white">{t.name}</div>
      <div className="text-xs text-slate-500">#{t.fifa_rank}</div>
    </div>
  );
}
