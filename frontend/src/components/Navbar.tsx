import { useState } from "react";
import { NavLink } from "react-router-dom";

export const REPO_URL = "https://github.com/shreyas463/2026-fifa-world-cup-final-predictor";

const LINKS = [
  { to: "/", label: "Home", end: true },
  { to: "/teams", label: "Teams" },
  { to: "/match", label: "Match Predictor" },
  { to: "/simulator", label: "Simulator" },
  { to: "/bracket", label: "Bracket" },
  { to: "/compare", label: "Compare" },
  { to: "/leaderboard", label: "Leaderboard" },
  { to: "/sentiment", label: "Sentiment" },
  { to: "/model", label: "Model Insights" },
];

export function GithubIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor" aria-hidden="true" className={className}>
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-lg px-3 py-2 text-sm font-medium transition ${
      isActive ? "bg-pitch-500/20 text-pitch-400" : "text-slate-300 hover:bg-white/5 hover:text-white"
    }`;

  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-night-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <NavLink to="/" className="flex items-center gap-2 font-bold text-white" onClick={() => setOpen(false)}>
          <span className="text-2xl">🏆</span>
          <span className="hidden sm:inline">
            WC<span className="text-pitch-400">2026</span> Predictor
          </span>
        </NavLink>

        <div className="flex items-center gap-1">
          <nav className="hidden items-center gap-1 lg:flex">
            {LINKS.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
                {l.label}
              </NavLink>
            ))}
          </nav>

          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-ghost !px-2.5"
            title="View source on GitHub"
            aria-label="View source on GitHub"
          >
            <GithubIcon />
            <span className="hidden xl:inline">GitHub</span>
          </a>

          <button
            className="btn-ghost !px-2.5 lg:hidden"
            onClick={() => setOpen((o) => !o)}
            aria-label="Toggle navigation menu"
            aria-expanded={open}
          >
            {open ? "✕" : "☰"}
          </button>
        </div>
      </div>

      {open && (
        <nav className="grid grid-cols-2 gap-1 border-t border-white/5 px-4 py-3 lg:hidden">
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass} onClick={() => setOpen(false)}>
              {l.label}
            </NavLink>
          ))}
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="col-span-2 mt-1 flex items-center justify-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-white/5"
            onClick={() => setOpen(false)}
          >
            <GithubIcon /> View source on GitHub
          </a>
        </nav>
      )}
    </header>
  );
}
