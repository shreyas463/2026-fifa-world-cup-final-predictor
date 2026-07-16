import { useState } from "react";
import { KnockoutMatch, Team } from "../api";

interface Props {
  rounds: { name: string; matches: KnockoutMatch[] }[];
  champion: Team | { id: number; name: string; flag: string };
  onSelectMatch?: (m: KnockoutMatch) => void;
}

// Horizontally-scrollable knockout bracket. Columns share height so matches
// centre into the classic pyramid; the advancing side is accented.
export default function BracketView({ rounds, champion, onSelectMatch }: Props) {
  const [active, setActive] = useState<KnockoutMatch | null>(null);

  const handle = (m: KnockoutMatch) => {
    setActive(m);
    onSelectMatch?.(m);
  };

  return (
    <div>
      <div className="overflow-x-auto pb-2">
        <div className="flex min-w-max items-stretch gap-3 md:gap-5">
          {rounds.map((round) => (
            <div key={round.name} className="flex min-w-[13.5rem] flex-col">
              <div className="mb-3 text-center">
                <span className="eyebrow">{round.name}</span>
              </div>
              <div className="flex flex-1 flex-col justify-around gap-3">
                {round.matches.map((m, i) => (
                  <button
                    key={i}
                    onClick={() => handle(m)}
                    className={`w-full overflow-hidden rounded-xl border text-left transition ${
                      active === m
                        ? "border-pitch-400 ring-1 ring-pitch-400/40"
                        : "border-white/10 bg-night-900/60 hover:border-white/25"
                    }`}
                  >
                    <TeamLine m={m} side="a" />
                    <div className="h-px bg-white/[0.06]" />
                    <TeamLine m={m} side="b" />
                  </button>
                ))}
              </div>
            </div>
          ))}

          <div className="flex min-w-[12rem] flex-col">
            <div className="mb-3 text-center">
              <span className="eyebrow text-gold">Champion</span>
            </div>
            <div className="flex flex-1 items-center">
              <div className="w-full rounded-xl border border-gold/40 bg-gradient-to-b from-gold/[0.15] to-gold/[0.04] p-4 text-center">
                <div className="text-4xl">{champion.flag}</div>
                <div className="mt-1 font-bold text-white">{champion.name}</div>
                <div className="mt-1 text-xl">🏆</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {active && (
        <div className="mt-3 rounded-xl border border-white/10 bg-white/[0.03] p-3.5 text-sm">
          <div className="mb-0.5 font-semibold text-white">
            {active.round}: {active.team_a.name} vs {active.team_b.name}
          </div>
          <div className="text-slate-400">
            {active.score_a != null ? (
              <>
                Result {active.score_a}–{active.score_b}
                {active.penalties ? " (after penalties)" : ""} · Winner:{" "}
                <span className="text-pitch-400">
                  {active.winner_id === active.team_a.id ? active.team_a.name : active.team_b.name}
                </span>
              </>
            ) : (
              <>
                Projected winner:{" "}
                <span className="text-pitch-400">
                  {active.winner_id === active.team_a.id ? active.team_a.name : active.team_b.name}
                </span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function TeamLine({ m, side }: { m: KnockoutMatch; side: "a" | "b" }) {
  const team = side === "a" ? m.team_a : m.team_b;
  const score = side === "a" ? m.score_a : m.score_b;
  const winner = m.winner_id === team.id;
  return (
    <div className={`flex items-center gap-2 px-2.5 py-2 ${winner ? "bg-pitch-500/[0.08]" : ""}`}>
      <span className={`h-4 w-[3px] rounded-full ${winner ? "bg-pitch-400" : "bg-transparent"}`} />
      <span className="text-base leading-none">{team.flag}</span>
      <span className={`flex-1 truncate text-[13px] ${winner ? "font-semibold text-white" : "text-slate-500"}`}>
        {team.name}
      </span>
      {m.penalties && winner && (
        <span className="rounded bg-gold/20 px-1 text-[9px] font-bold uppercase text-gold">pen</span>
      )}
      {score != null && (
        <span className={`font-mono text-sm ${winner ? "text-white" : "text-slate-500"}`}>{score}</span>
      )}
    </div>
  );
}
