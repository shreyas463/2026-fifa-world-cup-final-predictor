import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, pct, Team } from "../api";
import { useAsync } from "../hooks";
import { Disclaimer, ErrorMessage, Flag, Loader, ProbabilityBar, SectionTitle } from "../components/ui";

type SortKey = "winner" | "group_advance" | "final" | "rating" | "form";

export default function Teams() {
  const { data, loading, error, reload } = useAsync(() => api.teams(), []);
  const [q, setQ] = useState("");
  const [group, setGroup] = useState("");
  const [conf, setConf] = useState("");
  const [sort, setSort] = useState<SortKey>("winner");

  const confederations = useMemo(
    () => Array.from(new Set(data?.teams.map((t) => t.confederation) ?? [])).sort(),
    [data]
  );
  const groups = useMemo(
    () => Array.from(new Set(data?.teams.map((t) => t.group) ?? [])).sort(),
    [data]
  );

  const teams = useMemo(() => {
    let list = (data?.teams ?? []).filter((t) => {
      if (q && !t.name.toLowerCase().includes(q.toLowerCase())) return false;
      if (group && t.group !== group) return false;
      if (conf && t.confederation !== conf) return false;
      return true;
    });
    const key = (t: Team) =>
      sort === "rating" ? t.fifa_points : sort === "form" ? t.form : t.probabilities[sort];
    return [...list].sort((a, b) => key(b) - key(a));
  }, [data, q, group, conf, sort]);

  return (
    <div>
      <SectionTitle
        title="Team Predictions"
        subtitle="Search, filter and sort all 48 nations by their tournament probabilities."
      />

      <div className="card mb-6 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
        <input
          className="input"
          placeholder="🔍 Search team…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search team by name"
        />
        <select className="input" value={group} onChange={(e) => setGroup(e.target.value)} aria-label="Filter by group">
          <option value="">All groups</option>
          {groups.map((g) => (
            <option key={g} value={g}>
              Group {g}
            </option>
          ))}
        </select>
        <select className="input" value={conf} onChange={(e) => setConf(e.target.value)} aria-label="Filter by confederation">
          <option value="">All confederations</option>
          {confederations.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select className="input" value={sort} onChange={(e) => setSort(e.target.value as SortKey)} aria-label="Sort teams">
          <option value="winner">Sort: Win World Cup</option>
          <option value="final">Sort: Reach final</option>
          <option value="group_advance">Sort: Advance from group</option>
          <option value="rating">Sort: FIFA points</option>
          <option value="form">Sort: Recent form</option>
        </select>
      </div>

      {loading && <Loader />}
      {error && <ErrorMessage message={error} onRetry={reload} />}

      {data && (
        <>
          <div className="mb-3 text-sm text-slate-400">
            {teams.length} team{teams.length !== 1 ? "s" : ""}
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {teams.map((t) => (
              <Link key={t.id} to={`/teams/${t.id}`} className="card group p-4 transition hover:ring-1 hover:ring-pitch-400/40">
                <div className="flex items-center gap-3">
                  <div className="text-4xl">
                    <Flag flag={t.flag} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5 font-semibold text-white">
                      <span className="truncate">{t.name}</span>
                      {t.host && <span className="chip !px-1.5 !py-0 text-[10px]">HOST</span>}
                    </div>
                    <div className="text-xs text-slate-500">
                      #{t.fifa_rank} · {t.confederation} · Grp {t.group}
                    </div>
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  <ProbabilityBar value={t.probabilities.winner} label="Win World Cup" color="#f4c542" />
                  <ProbabilityBar value={t.probabilities.group_advance} label="Advance from group" color="#12a150" />
                </div>
                <div className="mt-3 flex justify-between text-xs text-slate-500">
                  <span>FIFA {Math.round(t.fifa_points)}</span>
                  <span>💬 {Math.round(t.sentiment)}</span>
                  <span>Form {t.form}</span>
                </div>
              </Link>
            ))}
          </div>
          {teams.length === 0 && (
            <div className="card p-10 text-center text-slate-400">No teams match your filters.</div>
          )}
          <Disclaimer text={data.disclaimer} />
        </>
      )}
    </div>
  );
}
