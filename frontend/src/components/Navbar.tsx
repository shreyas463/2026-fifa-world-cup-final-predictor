import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

export const REPO_URL = "https://github.com/shreyas463/2026-fifa-world-cup-final-predictor";

const LINKS = [
  { to: "/", label: "Home", end: true, icon: "🏠" },
  { to: "/teams", label: "Teams", icon: "🌍" },
  { to: "/match", label: "Match Predictor", icon: "🎯" },
  { to: "/simulator", label: "Simulator", icon: "🎲" },
  { to: "/bracket", label: "Bracket", icon: "🗺️" },
  { to: "/compare", label: "Compare", icon: "⚖️" },
  { to: "/leaderboard", label: "Leaderboard", icon: "📊" },
  { to: "/sentiment", label: "Sentiment", icon: "💬" },
  { to: "/model", label: "Model Insights", icon: "🧠" },
];

export function GithubIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor" aria-hidden="true" className={className}>
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  const current = LINKS.find((l) => (l.to === "/" ? pathname === "/" : pathname.startsWith(l.to))) ?? LINKS[0];

  // Close on navigation; Esc to close + lock body scroll while open.
  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-white/5 bg-night-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <NavLink to="/" className="flex items-center gap-2 font-bold text-white">
            <span className="text-2xl">🏆</span>
            <span className="hidden sm:inline">
              WC<span className="text-pitch-400">2026</span> Predictor
            </span>
          </NavLink>

          {/* Current page indicator — you always know where you are */}
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <span className="text-base">{current.icon}</span>
            <span className="font-medium">{current.label}</span>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost !px-2.5"
              title="View source on GitHub"
              aria-label="View source on GitHub"
            >
              <GithubIcon />
            </a>
            <button className="btn-ghost gap-2 !px-3" onClick={() => setOpen(true)} aria-label="Open menu" aria-expanded={open}>
              <MenuIcon />
              <span className="hidden sm:inline">Menu</span>
            </button>
          </div>
        </div>
      </header>

      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={() => setOpen(false)}
        aria-hidden
      />

      {/* Slide-in drawer */}
      <aside
        className={`fixed right-0 top-0 z-50 flex h-full w-[300px] max-w-[85vw] flex-col border-l border-white/10 bg-night-950 shadow-2xl shadow-black/50 transition-transform duration-300 ease-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
        aria-hidden={!open}
      >
        <div className="flex items-center justify-between border-b border-white/5 px-5 py-4">
          <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Navigate</span>
          <button className="btn-ghost !px-2.5 !py-1.5" onClick={() => setOpen(false)} aria-label="Close menu">
            ✕
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-3">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `mb-0.5 flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
                  isActive
                    ? "bg-pitch-500/15 text-pitch-400 ring-1 ring-pitch-400/30"
                    : "text-slate-300 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <span className="text-lg leading-none">{l.icon}</span>
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/5 p-4">
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 rounded-xl border border-white/10 px-3 py-2.5 text-sm font-medium text-slate-300 hover:bg-white/5 hover:text-white"
          >
            <GithubIcon /> View source on GitHub
          </a>
          <p className="mt-3 text-center text-[11px] text-slate-500">
            Probability-based estimates · Not affiliated with FIFA
          </p>
        </div>
      </aside>
    </>
  );
}
