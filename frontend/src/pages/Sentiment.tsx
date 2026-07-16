import {
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { api, pct, SentimentRow } from "../api";
import { useAsync } from "../hooks";
import { Disclaimer, ErrorMessage, Loader, SectionTitle, StatCard } from "../components/ui";

const moodColor = (m: string) =>
  m === "euphoric" ? "#f4c542" : m === "optimistic" ? "#12a150" : m === "cautious" ? "#3b82f6" : "#ef4444";

export default function Sentiment() {
  const { data, loading, error, reload } = useAsync(() => api.sentiment(), []);

  if (loading) return <Loader label="Analysing fan chatter…" />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;
  if (!data) return null;

  const totalPosts = data.sentiment.reduce((s, r) => s + r.sample_posts, 0);
  const scatterData = data.sentiment.map((r) => ({ x: r.buzz, y: r.positivity, z: r.sample_posts, ...r }));

  return (
    <div>
      <SectionTitle
        title="Fan Sentiment Predictor"
        subtitle="Social-media positivity, conversation volume and momentum for every nation."
      />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Most positive" value={`${data.most_positive.flag} ${data.most_positive.name}`} sub={`${Math.round(data.most_positive.positivity)}/100 positivity`} accent />
        <StatCard label="Most talked about" value={`${data.most_buzz.flag} ${data.most_buzz.name}`} sub={`${Math.round(data.most_buzz.buzz)}/100 buzz`} />
        <StatCard label="Teams tracked" value={data.sentiment.length} />
        <StatCard label="Posts analysed" value={totalPosts.toLocaleString()} />
      </div>

      <div className="card mb-6 p-6">
        <h3 className="mb-1 font-semibold text-white">Buzz vs positivity</h3>
        <p className="mb-3 text-xs text-slate-400">
          Right = more conversation, up = more optimistic. Bubble size ≈ posts analysed.
        </p>
        <ResponsiveContainer width="100%" height={340}>
          <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis type="number" dataKey="x" name="Buzz" domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }}
              label={{ value: "Buzz", position: "insideBottom", offset: -8, fill: "#64748b", fontSize: 11 }} />
            <YAxis type="number" dataKey="y" name="Positivity" domain={[40, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }}
              label={{ value: "Positivity", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 11 }} />
            <ZAxis type="number" dataKey="z" range={[40, 400]} />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{ background: "#0d1424", border: "1px solid rgba(255,255,255,0.1)" }}
              formatter={(v: number, n: string) => [Math.round(v), n]}
              labelFormatter={() => ""}
              content={({ payload }) => {
                if (!payload || !payload.length) return null;
                const r = payload[0].payload as SentimentRow;
                return (
                  <div className="rounded-lg border border-white/10 bg-night-850 p-2 text-xs">
                    <div className="font-semibold text-white">{r.flag} {r.name}</div>
                    <div className="text-slate-400">positivity {Math.round(r.positivity)} · buzz {Math.round(r.buzz)}</div>
                    <div className="text-slate-400">{r.mood} · {r.momentum}</div>
                  </div>
                );
              }}
            />
            <Scatter data={scatterData}>
              {scatterData.map((r, i) => (
                <Cell key={i} fill={moodColor(r.mood)} fillOpacity={0.75} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="p-3">Team</th>
              <th className="p-3">Positivity</th>
              <th className="p-3 text-right">Buzz</th>
              <th className="p-3 text-right">Trend</th>
              <th className="p-3">Mood</th>
              <th className="p-3 text-right">Title odds</th>
            </tr>
          </thead>
          <tbody>
            {data.sentiment.map((r) => (
              <tr key={r.id} className="border-b border-white/5 hover:bg-white/5">
                <td className="p-3 font-medium text-white">
                  <span className="mr-2 text-lg">{r.flag}</span>
                  {r.name}
                </td>
                <td className="w-48 p-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/10">
                      <div className="h-full rounded-full" style={{ width: `${r.positivity}%`, background: moodColor(r.mood) }} />
                    </div>
                    <span className="w-8 text-right tabular-nums text-slate-400">{Math.round(r.positivity)}</span>
                  </div>
                </td>
                <td className="p-3 text-right tabular-nums text-slate-300">{Math.round(r.buzz)}</td>
                <td className={`p-3 text-right tabular-nums ${r.trend > 3 ? "text-pitch-400" : r.trend < -3 ? "text-red-400" : "text-slate-400"}`}>
                  {r.trend > 0 ? "▲" : r.trend < 0 ? "▼" : "–"} {Math.abs(r.trend)}
                </td>
                <td className="p-3">
                  <span className="chip capitalize" style={{ color: moodColor(r.mood) }}>{r.mood}</span>
                </td>
                <td className="p-3 text-right tabular-nums text-pitch-400">{pct(r.win_probability)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-4 text-xs text-slate-500">📡 Source: {data.source}</p>
      <Disclaimer text={data.disclaimer} />
    </div>
  );
}
