"""Feature engineering shared by training and inference.

The identical `build_feature_row` is used to label historical matches during
training AND to score a live matchup, so the model always sees inputs built the
same way. Every feature is derived only from information observable *before*
kickoff — no post-match data leaks in.
"""
from __future__ import annotations

from dataclasses import dataclass

# Column order the models are trained on.
FEATURE_NAMES = [
    "rating_diff",        # FIFA-points(A) - FIFA-points(B)
    "form_diff",          # recent-form(A) - recent-form(B)
    "attack_a",           # A goals-scored rate
    "defense_a",          # A goals-conceded rate
    "attack_b",           # B goals-scored rate
    "defense_b",          # B goals-conceded rate
    "attack_vs_defense",  # net attacking edge of A over B
    "h2h_diff",           # recent head-to-head goal difference (A perspective)
    "experience_diff",    # World Cup pedigree (titles*3 + appearances)
    "squad_diff",         # squad market-value difference
    "availability_diff",  # squad fitness / injury availability difference
    "sentiment_diff",     # social-media fan-positivity difference
    "home_advantage",     # +1 A host, -1 B host, 0 neutral
]

HOME_ADV_RATING = 65.0  # ranking-point bump applied to the host / home side


@dataclass
class TeamStats:
    """The minimal pre-match snapshot a matchup needs."""
    rating: float        # FIFA ranking points
    form: float          # 0-100 recent-form score
    attack: float        # goals scored per match vs average side
    defense: float       # goals conceded per match vs average side
    experience: float = 0.0    # WC pedigree score
    squad: float = 0.0         # squad value (€M)
    availability: float = 90.0 # 0-100 squad fitness
    sentiment: float = 60.0    # 0-100 fan positivity


def build_feature_row(a: TeamStats, b: TeamStats, home_advantage: int = 0,
                      h2h: float = 0.0) -> list[float]:
    """Vectorise a matchup from A's perspective. `home_advantage` in {-1,0,1}."""
    return [
        a.rating - b.rating,
        a.form - b.form,
        a.attack,
        a.defense,
        b.attack,
        b.defense,
        (a.attack - b.defense) - (b.attack - a.defense),
        h2h,
        a.experience - b.experience,
        (a.squad - b.squad) / 100.0,        # scale €M to keep magnitudes sane
        a.availability - b.availability,
        a.sentiment - b.sentiment,
        float(home_advantage),
    ]


def team_experience(wc_titles: int, wc_appearances: int) -> float:
    return float(wc_titles * 3 + wc_appearances)
