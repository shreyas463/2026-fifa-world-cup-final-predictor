import { api, pct } from "../api";
import { useAsync } from "../hooks";
import { Disclaimer, ErrorMessage, Loader, ProbabilityBar, SectionTitle } from "../components/ui";
import { Link } from "react-router-dom";

export default function Leaderboard() {
  const { data, loading, error, reload } = useAsync(() => api.predictions(), []);

  return (
    <div>
      <div className="flex items-center justify-between">
        <SectionTitle
          title="Prediction Leaderboard"
          subtitle="Every nation ranked by championship probability, based on 5,000 tournament simulations."
        />
        <button className="btn-ghost" onClick={reload} title="Refresh predictions">
          ↻ Refresh
        </button>
      </div>

      {loading && <Loader />}
      {error && <ErrorMessage message={error} onRetry={reload} />}

      {data && (
        <>
          <div className="card overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wide text-slate-400">
                  <th className="p-3">#</th>
                  <th className="p-3">Team</th>
                  <th className="p-3 text-right">FIFA pts</th>
                  <th className="p-3 text-right">Form</th>
                  <th className="p-3 text-right">Knockouts</th>
                  <th className="p-3 text-right">Final</th>
                  <th className="p-3 text-right">Win</th>
                  <th className="hidden p-3 md:table-cell">Title chance</th>
                </tr>
              </thead>
              <tbody>
                {data.leaderboard.map((t, i) => (
                  <tr key={t.id} className="border-b border-white/5 transition hover:bg-white/5">
                    <td className="p-3 font-bold text-slate-500">{i + 1}</td>
                    <td className="p-3">
                      <Link to={`/teams/${t.id}`} className="flex items-center gap-2 font-medium text-white hover:text-pitch-400">
                        <span className="text-xl">{t.flag}</span>
                        {t.name}
                        {t.host && <span className="chip !px-1.5 !py-0 text-[10px]">HOST</span>}
                      </Link>
                    </td>
                    <td className="p-3 text-right tabular-nums text-slate-300">{Math.round(t.fifa_points)}</td>
                    <td className="p-3 text-right tabular-nums text-slate-300">{t.form}</td>
                    <td className="p-3 text-right tabular-nums text-slate-300">{pct(t.probabilities.group_advance)}</td>
                    <td className="p-3 text-right tabular-nums text-slate-300">{pct(t.probabilities.final)}</td>
                    <td className="p-3 text-right font-bold tabular-nums text-pitch-400">{pct(t.probabilities.winner)}</td>
                    <td className="hidden w-40 p-3 md:table-cell">
                      <ProbabilityBar value={t.probabilities.winner} color={i === 0 ? "#f4c542" : "#12a150"} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Disclaimer text={data.disclaimer} />
        </>
      )}
    </div>
  );
}
