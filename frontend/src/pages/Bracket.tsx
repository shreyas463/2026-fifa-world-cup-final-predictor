import { api, KnockoutMatch } from "../api";
import { useAsync } from "../hooks";
import BracketView from "../components/BracketView";
import { Disclaimer, ErrorMessage, Loader, SectionTitle } from "../components/ui";

export default function Bracket() {
  const { data, loading, error, reload } = useAsync(() => api.bracket(), []);

  if (loading) return <Loader />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;
  if (!data) return null;
  const b = data.bracket;

  // Append the Final as a last round column so the bracket reads left-to-right.
  const rounds = [...b.knockout, { name: "Final", dates: b.final.dates, matches: [b.final] }];

  return (
    <div>
      <SectionTitle
        title="Tournament Bracket"
        subtitle="The full knockout path to the 2026 title. Click any match for details."
      />

      {/* Schedule strip */}
      <div className="card mb-6 flex flex-wrap items-center gap-2 p-4 text-xs">
        {b.schedule.map((s) => {
          const highlight = s.round === "Final" || s.round === "Third-place play-off";
          return (
            <div
              key={s.round}
              className={`rounded-lg px-3 py-2 ${
                highlight ? "bg-gold/15 text-amber-200 ring-1 ring-gold/30" : "bg-white/5 text-slate-400"
              }`}
            >
              <div className="font-semibold">{s.round}</div>
              <div>{s.dates}</div>
            </div>
          );
        })}
      </div>

      {/* Podium */}
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <PodiumCard place="Champions" emoji="🥇" flag={b.champion.flag} name={b.champion.name} accent />
        <PodiumCard place="Runners-up" emoji="🥈" flag={b.runner_up.flag} name={b.runner_up.name} />
        <PodiumCard place="Third place" emoji="🥉" flag={b.third.flag} name={b.third.name} />
      </div>

      <div className="card p-6">
        <BracketView rounds={rounds} champion={b.champion} />
      </div>

      {/* Final & third place */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <FeaturedMatch title="🏆 Final" subtitle={b.final.dates} m={b.final} />
        <FeaturedMatch title="🥉 Third-place play-off" subtitle={b.third_place.dates} m={b.third_place} />
      </div>

      <div className="mt-6 card p-6">
        <h2 className="mb-4 text-lg font-semibold text-white">Group qualifiers</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Object.entries(b.groups).map(([g, rows]) => (
            <div key={g} className="rounded-xl border border-white/5 bg-night-900 p-3">
              <div className="mb-2 text-sm font-semibold text-slate-300">Group {g}</div>
              <ul className="space-y-1 text-sm">
                {rows.map((r) => (
                  <li key={r.id} className={`flex items-center gap-2 ${r.qualified ? "text-white" : "text-slate-500"}`}>
                    <span>{r.flag}</span>
                    <span className="flex-1 truncate">{r.name}</span>
                    {r.qualified && (
                      <span className="chip !px-1.5 !py-0 text-[10px]">
                        {r.position === "3" ? "3rd" : r.position}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {b.is_projection && (
        <p className="mt-4 text-center text-xs text-slate-500">
          Bracket is a deterministic projection (favourite advances; one scripted semifinal upset to reach the
          specified final). Scorelines are model-projected, not verified match results — edit the data file to drop in
          real scores.
        </p>
      )}

      <Disclaimer text={data.disclaimer} />
    </div>
  );
}

function PodiumCard({
  place,
  emoji,
  flag,
  name,
  accent,
}: {
  place: string;
  emoji: string;
  flag: string;
  name: string;
  accent?: boolean;
}) {
  return (
    <div className={`card p-5 text-center ${accent ? "ring-1 ring-gold/40" : ""}`}>
      <div className="text-xs uppercase tracking-wide text-slate-400">
        {emoji} {place}
      </div>
      <div className="my-2 text-5xl">{flag}</div>
      <div className={`font-bold ${accent ? "text-gold" : "text-white"}`}>{name}</div>
    </div>
  );
}

function FeaturedMatch({ title, subtitle, m }: { title: string; subtitle: string; m: KnockoutMatch }) {
  const winA = m.winner_id === m.team_a.id;
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-white">{title}</h3>
        <span className="text-xs text-slate-400">{subtitle}</span>
      </div>
      <div className="flex items-center justify-between">
        <Side flag={m.team_a.flag} name={m.team_a.name} win={winA} />
        <div className="px-4 text-center">
          <div className="text-3xl font-extrabold text-white">
            {m.score_a} – {m.score_b}
          </div>
          {m.penalties && <div className="text-xs text-gold">on penalties</div>}
        </div>
        <Side flag={m.team_b.flag} name={m.team_b.name} win={!winA} right />
      </div>
    </div>
  );
}

function Side({ flag, name, win, right }: { flag: string; name: string; win: boolean; right?: boolean }) {
  return (
    <div className={`flex items-center gap-2 ${right ? "flex-row-reverse text-right" : ""}`}>
      <span className="text-4xl">{flag}</span>
      <span className={`font-semibold ${win ? "text-pitch-400" : "text-slate-400"}`}>{name}</span>
    </div>
  );
}
