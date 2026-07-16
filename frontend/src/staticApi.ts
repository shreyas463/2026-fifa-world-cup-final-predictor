// Static API client — serves pre-computed JSON so the app runs with no backend
// (e.g. on GitHub Pages). Enabled at build time via VITE_STATIC=true.
import type { MatchPrediction, ModelMetrics, SentimentRow, Team, TeamDetail } from "./api";

const DATA = `${import.meta.env.BASE_URL}data/`;
const DISCLAIMER =
  "All figures are probability-based statistical estimates, not guaranteed outcomes. " +
  "Real results are affected by injuries, squad changes, tactics, red cards, penalties and other unpredictable events.";

const cache: Record<string, Promise<any>> = {};
function load(name: string): Promise<any> {
  if (!cache[name]) {
    cache[name] = fetch(`${DATA}${name}.json`).then((r) => {
      if (!r.ok) throw new Error(`Could not load ${name}.json`);
      return r.json();
    });
  }
  return cache[name];
}

const pick = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

export const staticApi = {
  teams: async (params?: { q?: string; group?: string; confederation?: string }) => {
    let rows: Team[] = await load("teams");
    if (params?.q) rows = rows.filter((t) => t.name.toLowerCase().includes(params.q!.toLowerCase()));
    if (params?.group) rows = rows.filter((t) => t.group.toUpperCase() === params.group!.toUpperCase());
    if (params?.confederation)
      rows = rows.filter((t) => t.confederation.toLowerCase() === params.confederation!.toLowerCase());
    rows = [...rows].sort((a, b) => b.win_probability - a.win_probability);
    return { count: rows.length, teams: rows, disclaimer: DISCLAIMER };
  },

  team: async (id: number) => {
    const details: Record<string, TeamDetail> = await load("details");
    return { team: details[String(id)], disclaimer: DISCLAIMER };
  },

  predictions: async () => {
    const p = await load("predictions");
    return { ...p, disclaimer: DISCLAIMER };
  },

  predictMatch: async (team_a_id: number, team_b_id: number, _neutral = true) => {
    const matches: Record<string, MatchPrediction> = await load("matches");
    const pred = matches[`${team_a_id}-${team_b_id}`];
    if (!pred) throw new Error("Pick two different teams");
    return { prediction: pred, disclaimer: DISCLAIMER };
  },

  simulate: async (simulations: number, _seed?: number) => {
    const s = await load("sims");
    const sample = pick(s.samples);
    if (simulations === 1) {
      return { mode: "single" as const, simulation: sample, disclaimer: DISCLAIMER };
    }
    return {
      mode: "aggregate" as const,
      simulations,
      results: s.aggregate,
      sample_bracket: sample,
      disclaimer: DISCLAIMER,
    };
  },

  bracket: async () => {
    const bracket = await load("bracket");
    return { bracket, disclaimer: DISCLAIMER };
  },

  metrics: async () => {
    const metrics: ModelMetrics = await load("metrics");
    return { metrics, disclaimer: DISCLAIMER };
  },

  sentiment: async () => {
    const s = await load("sentiment");
    return { ...s, disclaimer: DISCLAIMER } as {
      sentiment: SentimentRow[];
      most_positive: SentimentRow;
      most_buzz: SentimentRow;
      source: string;
      disclaimer: string;
    };
  },

  comparison: async (team_a: number, team_b: number) => {
    const [details, matches] = await Promise.all([load("details"), load("matches")]);
    const m: MatchPrediction = matches[`${team_a}-${team_b}`];
    const a: TeamDetail = details[String(team_a)];
    const b: TeamDetail = details[String(team_b)];
    return {
      team_a: a,
      team_b: b,
      attribute_labels: a.attribute_labels,
      head_to_head: m.head_to_head,
      match_preview: m.probabilities,
      disclaimer: DISCLAIMER,
    };
  },
};
