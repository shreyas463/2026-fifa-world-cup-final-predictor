// Typed client for the World Cup prediction API.
const BASE = import.meta.env.VITE_API_URL ?? "";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed (${res.status}): ${path}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

// ---- Types -----------------------------------------------------------------
export interface StageProbs {
  r32: number;
  r16: number;
  qf: number;
  sf: number;
  final: number;
  winner: number;
  group_advance: number;
}

export interface Team {
  id: number;
  name: string;
  flag: string;
  confederation: string;
  elo: number;
  form: number;
  squad_value_m: number;
  wc_titles: number;
  wc_appearances: number;
  host: boolean;
  fifa_rank: number;
  group: string;
  attack: number;
  defense: number;
  probabilities: StageProbs;
  win_probability: number;
  rank?: number;
}

export interface TeamDetail extends Team {
  attributes: Record<string, number>;
  attribute_labels: Record<string, string>;
  strengths: string[];
  weaknesses: string[];
}

export interface MatchPrediction {
  team_a: Team;
  team_b: Team;
  neutral_venue: boolean;
  probabilities: { team_a_win: number; draw: number; team_b_win: number };
  expected_goals: { team_a: number; team_b: number };
  predicted_score: { team_a: number; team_b: number };
  head_to_head: { year: number; team_a: string; team_b: string; score_a: number; score_b: number }[];
  form_comparison: { team_a: number; team_b: number };
  ranking_comparison: { team_a: number; team_b: number };
  key_factors: { factor: string; favours: string; detail: string; weight: number }[];
  model: string;
}

export interface KnockoutMatch {
  round: string;
  team_a: { id: number; name: string; flag: string; group: string };
  team_b: { id: number; name: string; flag: string; group: string };
  score_a?: number;
  score_b?: number;
  penalties?: boolean;
  winner_id: number;
}

export interface Bracket {
  groups: Record<string, { id: number; name: string; flag: string; qualified: boolean }[]>;
  knockout: { name: string; matches: KnockoutMatch[] }[];
  champion: Team;
}

export interface Simulation {
  seed: number | null;
  groups: Record<string, (Team & { points: number; gf: number; ga: number; gd: number; qualified: boolean })[]>;
  knockout: { name: string; matches: KnockoutMatch[] }[];
  champion: Team;
}

export interface ModelMetrics {
  best_model: string;
  metrics: Record<string, number>;
  model_comparison: Record<string, Record<string, number>>;
  confusion_matrix: { labels: string[]; matrix: number[][] };
  feature_importance: { feature: string; importance: number }[];
  calibration_curve: { predicted: number; observed: number; count: number }[];
  training: { n_matches: number; n_train: number; n_test: number; features: string[]; class_labels: string[] };
  data_sources: string[];
  limitations: string[];
}

export const api = {
  teams: (params?: { q?: string; group?: string; confederation?: string }) => {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.group) qs.set("group", params.group);
    if (params?.confederation) qs.set("confederation", params.confederation);
    const s = qs.toString();
    return get<{ count: number; teams: Team[]; disclaimer: string }>(`/api/teams${s ? `?${s}` : ""}`);
  },
  team: (id: number) => get<{ team: TeamDetail; disclaimer: string }>(`/api/teams/${id}`),
  predictions: () =>
    get<{ leaderboard: Team[]; favourite: Team; disclaimer: string }>(`/api/predictions`),
  predictMatch: (team_a_id: number, team_b_id: number, neutral = true) =>
    post<{ prediction: MatchPrediction; disclaimer: string }>(`/api/predict-match`, {
      team_a_id,
      team_b_id,
      neutral,
    }),
  simulate: (simulations: number, seed?: number) =>
    post<
      | { mode: "single"; simulation: Simulation; disclaimer: string }
      | { mode: "aggregate"; simulations: number; results: Team[]; sample_bracket: Simulation; disclaimer: string }
    >(`/api/simulate-tournament`, { simulations, seed }),
  bracket: () => get<{ bracket: Bracket; disclaimer: string }>(`/api/bracket`),
  metrics: () => get<{ metrics: ModelMetrics; disclaimer: string }>(`/api/model-metrics`),
  comparison: (team_a: number, team_b: number) =>
    get<{
      team_a: TeamDetail;
      team_b: TeamDetail;
      attribute_labels: Record<string, string>;
      head_to_head: MatchPrediction["head_to_head"];
      match_preview: { team_a_win: number; draw: number; team_b_win: number };
      disclaimer: string;
    }>(`/api/team-comparison?team_a=${team_a}&team_b=${team_b}`),
};

export const pct = (n: number) => `${(n * 100).toFixed(1)}%`;
