import { Link, useParams } from "react-router-dom";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import { api, pct } from "../api";
import { useAsync } from "../hooks";
import { Disclaimer, ErrorMessage, Flag, Loader, ProbabilityBar, StatCard } from "../components/ui";

const STAGE_ROWS: { key: keyof import("../api").StageProbs; label: string }[] = [
  { key: "group_advance", label: "Advance from group" },
  { key: "r32", label: "Reach Round of 32" },
  { key: "r16", label: "Reach Round of 16" },
  { key: "qf", label: "Reach Quarterfinals" },
  { key: "sf", label: "Reach Semifinals" },
  { key: "final", label: "Reach Final" },
  { key: "winner", label: "Win the World Cup" },
];

export default function TeamDetail() {
  const { id } = useParams();
  const { data, loading, error, reload } = useAsync(() => api.team(Number(id)), [id]);

  if (loading) return <Loader />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;
  if (!data) return null;
  const t = data.team;

  const radarData = Object.entries(t.attributes).map(([k, v]) => ({
    attribute: t.attribute_labels[k] ?? k,
    value: v,
  }));

  return (
    <div>
      <Link to="/teams" className="mb-4 inline-block text-sm text-slate-400 hover:text-white">
        ← Back to teams
      </Link>

      <div className="card mb-6 flex flex-wrap items-center gap-5 p-6">
        <div className="text-7xl">
          <Flag flag={t.flag} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-white">{t.name}</h1>
            {t.host && <span className="chip">HOST NATION</span>}
          </div>
          <div className="mt-1 text-sm text-slate-400">
            {t.confederation} · Group {t.group} · {t.wc_titles} World Cup titles · {t.wc_appearances} appearances
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs uppercase tracking-wide text-gold">Title chance</div>
          <div className="text-4xl font-extrabold text-pitch-400">{pct(t.probabilities.winner)}</div>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="FIFA / Elo rank" value={`#${t.fifa_rank}`} sub={`Elo ${t.elo}`} />
        <StatCard label="Recent form" value={t.form} sub="0–100 index" />
        <StatCard label="Squad value" value={`€${t.squad_value_m}M`} />
        <StatCard label="Win World Cup" value={pct(t.probabilities.winner)} accent />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h2 className="mb-4 text-lg font-semibold text-white">Path to the title</h2>
          <div className="space-y-3">
            {STAGE_ROWS.map((row) => (
              <ProbabilityBar
                key={row.key}
                value={t.probabilities[row.key]}
                label={row.label}
                color={row.key === "winner" ? "#f4c542" : "#12a150"}
              />
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h2 className="mb-2 text-lg font-semibold text-white">Team profile</h2>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData} outerRadius="72%">
              <PolarGrid stroke="rgba(255,255,255,0.12)" />
              <PolarAngleAxis dataKey="attribute" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Radar dataKey="value" stroke="#12a150" fill="#12a150" fillOpacity={0.4} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mt-6 grid gap-6 sm:grid-cols-2">
        <div className="card p-6">
          <h3 className="mb-3 flex items-center gap-2 font-semibold text-pitch-400">💪 Strongest attributes</h3>
          <ul className="space-y-2">
            {t.strengths.map((s) => (
              <li key={s} className="flex items-center gap-2 text-slate-200">
                <span className="text-pitch-400">▲</span> {s}
              </li>
            ))}
          </ul>
        </div>
        <div className="card p-6">
          <h3 className="mb-3 flex items-center gap-2 font-semibold text-amber-400">⚠️ Main weaknesses</h3>
          <ul className="space-y-2">
            {t.weaknesses.map((w) => (
              <li key={w} className="flex items-center gap-2 text-slate-200">
                <span className="text-amber-400">▼</span> {w}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link to="/compare" className="btn-ghost">
          Compare with another team
        </Link>
        <Link to="/match" className="btn-ghost">
          Predict a match
        </Link>
      </div>

      <Disclaimer text={data.disclaimer} />
    </div>
  );
}
