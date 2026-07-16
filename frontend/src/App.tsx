import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
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
      <footer className="border-t border-white/5 py-6 text-center text-xs text-slate-500">
        2026 FIFA World Cup Winner Predictor · Statistical estimates for educational use · Not affiliated with FIFA
      </footer>
    </div>
  );
}
