import { useState } from "react";
import { NavLink } from "react-router-dom";

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

        <nav className="hidden items-center gap-1 lg:flex">
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
              {l.label}
            </NavLink>
          ))}
        </nav>

        <button
          className="btn-ghost lg:hidden"
          onClick={() => setOpen((o) => !o)}
          aria-label="Toggle navigation menu"
          aria-expanded={open}
        >
          {open ? "✕" : "☰"}
        </button>
      </div>

      {open && (
        <nav className="grid grid-cols-2 gap-1 border-t border-white/5 px-4 py-3 lg:hidden">
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass} onClick={() => setOpen(false)}>
              {l.label}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  );
}
