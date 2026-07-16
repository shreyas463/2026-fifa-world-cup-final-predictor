import { useState } from "react";
import { KnockoutMatch, Team } from "../api";

interface Props {
  rounds: { name: string; matches: KnockoutMatch[] }[];
  champion: Team | { id: number; name: string; flag: string };
  onSelectMatch?: (m: KnockoutMatch) => void;
}

// Horizontally-scrollable knockout bracket. Each round is a column; matches
// show flags, scores (when available) and the advancing side highlighted.
export default function BracketView({ rounds, champion, onSelectMatch }: Props) {
  const [active, setActive] = useState<KnockoutMatch | null>(null);

  const handle = (m: KnockoutMatch) => {
    setActive(m);
    onSelectMatch?.(m);
  };

  return (
    <div>
      <div className="overflow-x-auto pb-4">
        <div className="flex min-w-max gap-6">
          {rounds.map((round) => (
            <div key={round.name} className="flex flex-col justify-around gap-4">
              <div className="sticky top-0 mb-1 text-center text-xs font-semibold uppercase tracking-wide text-slate-400">
                {round.name}
              </div>
              {round.matches.map((m, i) => (
                <button
                  key={i}
                  onClick={() => handle(m)}
                  className={`w-52 rounded-xl border p-2 text-left transition ${
                    active === m ? "border-pitch-400 bg-pitch-500/10" : "border-white/10 bg-night-900 hover:border-white/25"
                  }`}
                >
                  <TeamLine m={m} side="a" />
                  <div className="my-1 h-px bg-white/5" />
                  <TeamLine m={m} side="b" />
                </button>
              ))}
            </div>
          ))}
          <div className="flex flex-col justify-center">
            <div className="mb-1 text-center text-xs font-semibold uppercase tracking-wide text-gold">Champion</div>
            <div className="w-52 rounded-xl border border-gold/40 bg-gold/10 p-4 text-center">
              <div className="text-4xl">{champion.flag}</div>
              <div className="mt-1 font-bold text-white">{champion.name}</div>
              <div className="text-lg">🏆</div>
            </div>
          </div>
        </div>
      </div>

      {active && (
        <div className="card mt-2 p-4 text-sm">
          <div className="mb-1 font-semibold text-white">
            {active.round}: {active.team_a.name} vs {active.team_b.name}
          </div>
          <div className="text-slate-400">
            {active.score_a !== undefined ? (
              <>
                Result {active.score_a}–{active.score_b}
                {active.penalties ? " (after penalties)" : ""} · Winner:{" "}
                {active.winner_id === active.team_a.id ? active.team_a.name : active.team_b.name}
              </>
            ) : (
              <>Projected winner: {active.winner_id === active.team_a.id ? active.team_a.name : active.team_b.name}</>
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
    <div className={`flex items-center gap-2 ${winner ? "text-white" : "text-slate-500"}`}>
      <span className="text-lg">{team.flag}</span>
      <span className={`flex-1 truncate text-sm ${winner ? "font-semibold" : ""}`}>{team.name}</span>
      {score !== undefined && <span className="font-mono text-sm">{score}</span>}
      {winner && <span className="text-pitch-400">▸</span>}
    </div>
  );
}
