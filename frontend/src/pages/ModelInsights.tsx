import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { useAsync } from "../hooks";
import { Disclaimer, ErrorMessage, Loader, SectionTitle, StatCard } from "../components/ui";

const METRIC_HELP: Record<string, string> = {
  accuracy: "How often the top predicted outcome (win/draw/loss) is correct.",
  log_loss: "Penalty for confident wrong probabilities — lower is better.",
  precision: "Of predicted outcomes, how many were right (macro-averaged).",
  recall: "Of actual outcomes, how many were caught (macro-averaged).",
  f1: "Balance of precision and recall.",
  roc_auc: "Ability to rank outcomes correctly (0.5 = coin flip, 1 = perfect).",
  brier: "Mean squared error of the probabilities — lower is better.",
};

const AXIS = { fill: "#94a3b8", fontSize: 11 };

export default function ModelInsights() {
  const { data, loading, error, reload } = useAsync(() => api.metrics(), []);

  if (loading) return <Loader />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;
  if (!data) return null;
  const m = data.metrics;

  if (!m.metrics || Object.keys(m.metrics).length === 0) {
    return (
      <div>
        <SectionTitle title="Model Insights" />
        <div className="card p-8 text-center text-slate-400">
          No trained model found. Run <code className="text-pitch-400">python -m wc2026.ml.train</code> in the backend.
        </div>
      </div>
    );
  }

  const comparisonData = Object.entries(m.model_comparison).map(([name, mm]) => ({
    name: name.replace(" (baseline)", ""),
    accuracy: mm.accuracy,
    log_loss: mm.log_loss,
    roc_auc: mm.roc_auc,
  }));

  const maxImp = Math.max(...m.feature_importance.map((f) => f.importance));

  return (
    <div>
      <SectionTitle
        title="Model Insights"
        subtitle={`How the predictor works — best model: ${m.best_model}, trained on ${m.training.n_matches.toLocaleString()} matches.`}
      />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {Object.entries(m.metrics).map(([k, v]) => (
          <div key={k} className="card p-3" title={METRIC_HELP[k]}>
            <div className="text-[10px] uppercase tracking-wide text-slate-400">{k.replace("_", " ")}</div>
            <div className="mt-0.5 text-xl font-bold text-pitch-400">{v}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h3 className="mb-1 font-semibold text-white">Feature importance</h3>
          <p className="mb-3 text-xs text-slate-400">Which inputs the model relies on most.</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={m.feature_importance} layout="vertical" margin={{ left: 30 }}>
              <XAxis type="number" tick={AXIS} />
              <YAxis type="category" dataKey="feature" width={110} tick={AXIS} />
              <Tooltip contentStyle={{ background: "#0d1424", border: "1px solid rgba(255,255,255,0.1)" }} />
              <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                {m.feature_importance.map((f, i) => (
                  <Cell key={i} fill={f.importance === maxImp ? "#f4c542" : "#12a150"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6">
          <h3 className="mb-1 font-semibold text-white">Model comparison</h3>
          <p className="mb-3 text-xs text-slate-400">Accuracy and ROC-AUC across the models we trained.</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={comparisonData} margin={{ bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" tick={{ ...AXIS, fontSize: 10 }} interval={0} angle={-12} textAnchor="end" height={50} />
              <YAxis tick={AXIS} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: "#0d1424", border: "1px solid rgba(255,255,255,0.1)" }} />
              <Bar dataKey="accuracy" fill="#12a150" radius={[4, 4, 0, 0]} />
              <Bar dataKey="roc_auc" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6">
          <h3 className="mb-1 font-semibold text-white">Confusion matrix</h3>
          <p className="mb-3 text-xs text-slate-400">Predicted vs actual outcomes on the held-out test set.</p>
          <ConfusionMatrix cm={m.confusion_matrix} />
        </div>

        <div className="card p-6">
          <h3 className="mb-1 font-semibold text-white">Calibration curve</h3>
          <p className="mb-3 text-xs text-slate-400">
            Predicted vs observed win rate — the closer to the diagonal, the better-calibrated.
          </p>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={m.calibration_curve}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="predicted" type="number" domain={[0, 1]} tick={AXIS} />
              <YAxis type="number" domain={[0, 1]} tick={AXIS} />
              <Tooltip contentStyle={{ background: "#0d1424", border: "1px solid rgba(255,255,255,0.1)" }} />
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#475569"
                strokeDasharray="4 4"
                dot={false}
                name="perfect"
              />
              <Line type="monotone" dataKey="observed" stroke="#12a150" strokeWidth={2} name="model" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h3 className="mb-3 font-semibold text-white">📊 Data sources</h3>
          <ul className="space-y-2 text-sm text-slate-300">
            {m.data_sources.map((s) => (
              <li key={s} className="flex gap-2">
                <span className="text-pitch-400">•</span> {s}
              </li>
            ))}
          </ul>
        </div>
        <div className="card p-6">
          <h3 className="mb-3 font-semibold text-white">⚠️ Model limitations</h3>
          <ul className="space-y-2 text-sm text-slate-300">
            {m.limitations.map((s) => (
              <li key={s} className="flex gap-2">
                <span className="text-amber-400">•</span> {s}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <Disclaimer text={data.disclaimer} />
    </div>
  );
}

function ConfusionMatrix({ cm }: { cm: { labels: string[]; matrix: number[][] } }) {
  const max = Math.max(...cm.matrix.flat(), 1);
  return (
    <div className="overflow-x-auto">
      <table className="mx-auto text-center text-sm">
        <thead>
          <tr>
            <th className="p-2 text-xs text-slate-500">actual ↓ / pred →</th>
            {cm.labels.map((l) => (
              <th key={l} className="p-2 text-xs text-slate-400">
                {l}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cm.matrix.map((row, i) => (
            <tr key={i}>
              <td className="p-2 text-xs text-slate-400">{cm.labels[i]}</td>
              {row.map((v, j) => (
                <td key={j} className="p-1">
                  <div
                    className="flex h-12 w-16 items-center justify-center rounded-lg font-semibold text-white"
                    style={{ background: `rgba(18,161,80,${0.15 + (v / max) * 0.7})` }}
                  >
                    {v}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
