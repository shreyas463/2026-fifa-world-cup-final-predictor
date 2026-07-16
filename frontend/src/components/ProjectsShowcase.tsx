import { GithubIcon, REPO_URL } from "./Navbar";

interface Project {
  rank: string;
  emoji: string;
  name: string;
  desc: string;
  tags: string[];
  url: string;
  current?: boolean;
}

// Ordered best-first (see the project ranking).
const PROJECTS: Project[] = [
  {
    rank: "🥇",
    emoji: "🖥️",
    name: "RackLAB",
    desc: "A walkable, first-person 3D data-center simulator — live thermal, power-chain and cooling-failure scenarios, with a pure, unit-tested simulation core.",
    tags: ["TypeScript", "Three.js", "R3F", "Zustand", "Vitest"],
    url: "https://github.com/shreyas463/racklab",
  },
  {
    rank: "🥈",
    emoji: "🏆",
    name: "2026 World Cup Predictor",
    desc: "This app — full-stack ML on real historical results: Elo replay, a validated match model, Monte Carlo tournament simulation and a live match predictor.",
    tags: ["Python", "FastAPI", "scikit-learn", "React"],
    url: REPO_URL,
    current: true,
  },
  {
    rank: "🥉",
    emoji: "🤖",
    name: "autoresearch-macos",
    desc: "An autonomous ML-research harness: an agent iterates on training code overnight against a fixed 5-minute budget, scored by a single metric.",
    tags: ["Python", "PyTorch", "Apple Silicon"],
    url: "https://github.com/shreyas463/autoresearch-macos",
  },
];

export default function ProjectsShowcase() {
  return (
    <section className="mt-14">
      <div className="mb-1.5 flex items-center gap-2.5">
        <span className="h-6 w-1 rounded-full bg-pitch-500" />
        <h2 className="text-2xl font-bold tracking-tight text-white">Projects</h2>
      </div>
      <p className="mb-6 pl-3.5 text-sm text-slate-400">A few more things I've built — best first.</p>

      <div className="grid gap-4 md:grid-cols-3">
        {PROJECTS.map((p) => (
          <a
            key={p.name}
            href={p.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`card card-hover flex flex-col p-5 ${
              p.rank === "🥇" ? "ring-1 ring-gold/40" : ""
            }`}
          >
            <div className="mb-3 flex items-center justify-between">
              <span className="text-3xl leading-none">{p.emoji}</span>
              <span className="text-xl leading-none">{p.rank}</span>
            </div>
            <h3 className="flex flex-wrap items-center gap-2 font-bold text-white">
              {p.name}
              {p.current && (
                <span className="chip !px-2 !py-0.5 !text-[10px] text-pitch-400">You're here</span>
              )}
            </h3>
            <p className="mt-1.5 flex-1 text-sm leading-relaxed text-slate-400">{p.desc}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {p.tags.map((t) => (
                <span key={t} className="chip !px-2 !py-0.5 !text-[10px]">
                  {t}
                </span>
              ))}
            </div>
            <div className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-pitch-400">
              <GithubIcon /> View on GitHub →
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}
