"""Feature engineering shared by training and inference.

The exact same `build_feature_row` is used to (a) label historical matches
during training and (b) score a live matchup at prediction time, which
guarantees the model sees identically-constructed inputs in both phases.
"""
from __future__ import annotations

from dataclasses import dataclass

# Order matters: models are trained on this column order.
FEATURE_NAMES = [
    "elo_diff",          # Elo(A) - Elo(B)
    "form_diff",         # recent-form(A) - recent-form(B)
    "attack_a",          # A goals-scored rate
    "defense_a",         # A goals-conceded rate
    "attack_b",          # B goals-scored rate
    "defense_b",         # B goals-conceded rate
    "attack_vs_defense", # net attacking edge of A over B
    "home_advantage",    # +1 A host, -1 B host, 0 neutral
]

HOME_ADV_ELO = 65.0  # Elo bump applied to the host / home side in the match engine


@dataclass
class TeamStats:
    """The minimal, pre-match-observable snapshot a matchup needs."""
    elo: float
    form: float     # 0-100 recent-form score
    attack: float   # goals scored per match vs average side
    defense: float  # goals conceded per match vs average side


def build_feature_row(a: TeamStats, b: TeamStats, home_advantage: int = 0) -> list[float]:
    """Vectorise a matchup from A's perspective. `home_advantage` in {-1,0,1}."""
    return [
        a.elo - b.elo,
        a.form - b.form,
        a.attack,
        a.defense,
        b.attack,
        b.defense,
        (a.attack - b.defense) - (b.attack - a.defense),
        float(home_advantage),
    ]
