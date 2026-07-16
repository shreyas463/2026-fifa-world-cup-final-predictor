import { Link } from "react-router-dom";
import { api, pct } from "../api";
import { useAsync } from "../hooks";
import { Disclaimer, ErrorMessage, Flag, Loader, ProbabilityBar } from "../components/ui";
import ProjectsShowcase from "../components/ProjectsShowcase";

export default function Home() {
  const { data, loading, error, reload } = useAsync(() => api.predictions(), []);

  return (
    <div>
      <section className="relative overflow-hidden rounded-3xl border border-white/[0.07] bg-gradient-to-br from-night-900 to-night-950 px-6 py-12 text-center sm:py-16">
        <div className="pointer-events-none absolute inset-0 opacity-40 [background:radial-gradient(circle_at_50%_-20%,rgba(18,161,80,0.35),transparent_60%)]" />
        <div className="relative">
          <span className="chip mx-auto mb-4">⚽ 48 teams · 104 matches · June–July 2026</span>
          <h1 className="mx-auto max-w-3xl text-4xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-5xl">
            Who will win the <span className="text-pitch-400">2026 FIFA World Cup?</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-slate-300">
            A machine-learning engine rates every nation, predicts each match, and runs thousands of Monte Carlo
            tournament simulations to estimate every team's path to glory.
          </p>
        </div>
      </section>

      {loading && <Loader label="Simulating the tournament…" />}
      {error && <ErrorMessage message={error} onRetry={reload} />}

      {data && (
        <>
          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <div className="card relative overflow-hidden p-8 text-center lg:col-span-1">
              <div className="pointer-events-none absolute inset-0 opacity-60 [background:radial-gradient(circle_at_50%_0%,rgba(244,197,66,0.18),transparent_70%)]" />
              <div className="relative">
                <div className="text-xs uppercase tracking-widest text-gold">Predicted Champion</div>
                <div className="my-3 text-8xl leading-none">
                  <Flag flag={data.favourite.flag} />
                </div>
                <div className="text-2xl font-bold text-white">{data.favourite.name}</div>
                <div className="mt-1 text-sm text-slate-400">
                  FIFA rank #{data.favourite.fifa_rank} · Group {data.favourite.group}
                </div>
                <div className="mt-6 text-5xl font-extrabold text-pitch-400">
                  {pct(data.favourite.win_probability)}
                </div>
                <div className="text-xs uppercase tracking-wide text-slate-400">championship probability</div>
                <Link to="/teams" className="btn-primary mt-6 w-full">
                  Explore all predictions →
                </Link>
              </div>
            </div>

            <div className="card p-6 lg:col-span-2">
              <h2 className="mb-4 text-lg font-semibold text-white">Top 5 favourites</h2>
              <div className="space-y-4">
                {data.leaderboard.slice(0, 5).map((t, i) => (
                  <Link
                    to={`/teams/${t.id}`}
                    key={t.id}
                    className="flex items-center gap-4 rounded-xl px-2 py-1.5 transition hover:bg-white/5"
                  >
                    <div className="w-6 text-center font-bold text-slate-500">{i + 1}</div>
                    <div className="text-3xl">
                      <Flag flag={t.flag} />
                    </div>
                    <div className="w-32 shrink-0">
                      <div className="font-semibold text-white">{t.name}</div>
                      <div className="text-xs text-slate-500">Elo {Math.round(t.elo)}</div>
                    </div>
                    <div className="flex-1">
                      <ProbabilityBar value={t.win_probability} color={i === 0 ? "#f4c542" : "#12a150"} />
                    </div>
                    <div className="w-16 text-right font-bold tabular-nums text-pitch-400">
                      {pct(t.win_probability)}
                    </div>
                  </Link>
                ))}
              </div>
              <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  { to: "/match", label: "Predict a match", icon: "🎯" },
                  { to: "/simulator", label: "Run simulations", icon: "🎲" },
                  { to: "/bracket", label: "View bracket", icon: "🗺️" },
                  { to: "/model", label: "How it works", icon: "🧠" },
                ].map((c) => (
                  <Link key={c.to} to={c.to} className="btn-ghost flex-col !py-4 text-center text-sm">
                    <span className="text-xl">{c.icon}</span>
                    {c.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>

          <Disclaimer />
        </>
      )}

      <ProjectsShowcase />
    </div>
  );
}
