import { Route, Routes } from "react-router-dom";
import Navbar, { GithubIcon, REPO_URL } from "./components/Navbar";
import Home from "./pages/Home";
import Teams from "./pages/Teams";
import TeamDetail from "./pages/TeamDetail";
import MatchPredictor from "./pages/MatchPredictor";
import Simulator from "./pages/Simulator";
import Bracket from "./pages/Bracket";
import Compare from "./pages/Compare";
import Leaderboard from "./pages/Leaderboard";
import ModelInsights from "./pages/ModelInsights";
import Sentiment from "./pages/Sentiment";

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/teams" element={<Teams />} />
          <Route path="/teams/:id" element={<TeamDetail />} />
          <Route path="/match" element={<MatchPredictor />} />
          <Route path="/simulator" element={<Simulator />} />
          <Route path="/bracket" element={<Bracket />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/sentiment" element={<Sentiment />} />
          <Route path="/model" element={<ModelInsights />} />
          <Route path="*" element={<div className="py-20 text-center text-slate-400">Page not found.</div>} />
        </Routes>
      </main>
      <footer className="mt-8 border-t border-white/5 py-8 text-center text-xs text-slate-500">
        <a
          href={REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="mb-3 inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3.5 py-2 font-medium text-slate-300 transition hover:border-white/20 hover:text-white"
        >
          <GithubIcon /> View source on GitHub
        </a>
        <p>2026 FIFA World Cup Winner Predictor · Statistical estimates for educational use · Not affiliated with FIFA</p>
      </footer>
    </div>
  );
}
