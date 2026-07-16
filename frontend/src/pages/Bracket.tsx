import { api } from "../api";
import { useAsync } from "../hooks";
import BracketView from "../components/BracketView";
import { Disclaimer, ErrorMessage, Loader, SectionTitle } from "../components/ui";

export default function Bracket() {
  const { data, loading, error, reload } = useAsync(() => api.bracket(), []);

  if (loading) return <Loader />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;
  if (!data) return null;
  const b = data.bracket;

  return (
    <div>
      <SectionTitle
        title="Predicted Tournament Bracket"
        subtitle="The most-likely path from the group stage to the final, with the favourite advancing at each step. Click any match for details."
      />

      <div className="card p-6">
        <BracketView rounds={b.knockout} champion={b.champion} />
      </div>

      <div className="mt-6 card p-6">
        <h2 className="mb-4 text-lg font-semibold text-white">Projected group qualifiers</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Object.entries(b.groups).map(([g, rows]) => (
            <div key={g} className="rounded-xl border border-white/5 bg-night-900 p-3">
              <div className="mb-2 text-sm font-semibold text-slate-300">Group {g}</div>
              <ul className="space-y-1 text-sm">
                {rows.map((r) => (
                  <li key={r.id} className={`flex items-center gap-2 ${r.qualified ? "text-white" : "text-slate-500"}`}>
                    <span>{r.flag}</span>
                    <span className="flex-1 truncate">{r.name}</span>
                    {r.qualified && <span className="text-pitch-400">✓</span>}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <Disclaimer text={data.disclaimer} />
    </div>
  );
}
