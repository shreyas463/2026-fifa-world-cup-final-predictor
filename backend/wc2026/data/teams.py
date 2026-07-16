"""Real 2026 FIFA World Cup field — the actual 48 qualified teams, the real
Final Draw (5 Dec 2025) groups, and real FIFA/Coca-Cola ranking points.

Sources (fetched July 2026):
  * Final Draw groups A–L: FIFA.com / Wikipedia "2026 FIFA World Cup draw"
  * FIFA ranking points: FIFA-Coca Cola Men's World Ranking (July 2026 snapshot)
  * World Cup titles / appearances: historical record

`fifa_points` for eight lower-ranked / playoff qualifiers (Bosnia, Haiti,
Curaçao, New Zealand, Cape Verde, Iraq, Jordan, Ghana) are best real-world
estimates — they sit outside the published top-60 table; all are marked below.
Attacking / defensive rates are derived from ranking strength and recent form;
`availability` (squad fitness) and `sentiment` (fan positivity) are attached
from the injuries proxy and the social-media sentiment module respectively.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .sentiment import sentiment_for

# name, flag, confederation, group, fifa_points, form, squad_value_m, availability, wc_titles, wc_apps, host
# (est) = fifa_points is a real-world estimate (outside published top-60 table)
_RAW = [
    # Group A
    ("Mexico",                 "🇲🇽", "CONCACAF", "A", 1754.30, 66, 210, 90, 0, 18, True),
    ("South Africa",           "🇿🇦", "CAF",      "A", 1451.24, 60, 60,  88, 0, 4,  False),
    ("South Korea",            "🇰🇷", "AFC",      "A", 1558.72, 68, 180, 90, 0, 12, False),
    ("Czech Republic",         "🇨🇿", "UEFA",     "A", 1467.26, 58, 200, 89, 0, 10, False),
    # Group B
    ("Canada",                 "🇨🇦", "CONCACAF", "B", 1571.34, 65, 160, 91, 0, 3,  True),
    ("Bosnia and Herzegovina", "🇧🇦", "UEFA",     "B", 1465.00, 60, 180, 87, 0, 2,  False),  # (est)
    ("Qatar",                  "🇶🇦", "AFC",      "B", 1411.06, 61, 40,  92, 0, 3,  False),
    ("Switzerland",            "🇨🇭", "UEFA",     "B", 1710.88, 66, 300, 90, 0, 13, False),
    # Group C
    ("Brazil",                 "🇧🇷", "CONMEBOL", "C", 1804.92, 80, 800, 89, 5, 23, False),
    ("Morocco",                "🇲🇦", "CAF",      "C", 1803.99, 82, 320, 91, 0, 7,  False),
    ("Haiti",                  "🇭🇹", "CONCACAF", "C", 1320.00, 52, 30,  86, 0, 2,  False),  # (est)
    ("Scotland",               "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "UEFA",     "C", 1491.22, 64, 200, 88, 0, 9,  False),
    # Group D
    ("USA",                    "🇺🇸", "CONCACAF", "D", 1690.33, 70, 260, 92, 0, 12, True),
    ("Paraguay",               "🇵🇾", "CONMEBOL", "D", 1542.48, 66, 120, 89, 0, 9,  False),
    ("Australia",              "🇦🇺", "AFC",      "D", 1581.51, 63, 90,  88, 0, 7,  False),
    ("Turkey",                 "🇹🇷", "UEFA",     "D", 1582.54, 72, 320, 90, 0, 6,  False),
    # Group E
    ("Germany",                "🇩🇪", "UEFA",     "E", 1726.22, 74, 900, 86, 4, 21, False),
    ("Curacao",                "🇨🇼", "CONCACAF", "E", 1335.00, 57, 25,  85, 0, 1,  False),  # (est)
    ("Ivory Coast",            "🇨🇮", "CAF",      "E", 1565.47, 67, 260, 89, 0, 4,  False),
    ("Ecuador",                "🇪🇨", "CONMEBOL", "E", 1592.59, 70, 220, 90, 0, 5,  False),
    # Group F
    ("Netherlands",            "🇳🇱", "UEFA",     "F", 1775.54, 77, 700, 88, 0, 12, False),
    ("Japan",                  "🇯🇵", "AFC",      "F", 1673.68, 79, 260, 92, 0, 8,  False),
    ("Sweden",                 "🇸🇪", "UEFA",     "F", 1525.58, 60, 260, 88, 0, 13, False),
    ("Tunisia",                "🇹🇳", "CAF",      "F", 1426.58, 58, 60,  89, 0, 7,  False),
    # Group G
    ("Belgium",                "🇧🇪", "UEFA",     "G", 1778.36, 68, 450, 87, 0, 15, False),
    ("Egypt",                  "🇪🇬", "CAF",      "G", 1597.04, 69, 160, 90, 0, 4,  False),
    ("Iran",                   "🇮🇷", "AFC",      "G", 1609.85, 66, 60,  90, 0, 7,  False),
    ("New Zealand",            "🇳🇿", "OFC",      "G", 1300.00, 58, 30,  88, 0, 3,  False),  # (est)
    # Group H
    ("Spain",                  "🇪🇸", "UEFA",     "H", 1912.34, 90, 1000, 92, 1, 17, False),
    ("Cape Verde",             "🇨🇻", "CAF",      "H", 1385.00, 66, 60,  87, 0, 1,  False),  # (est)
    ("Saudi Arabia",           "🇸🇦", "AFC",      "H", 1425.52, 56, 40,  90, 0, 7,  False),
    ("Uruguay",                "🇺🇾", "CONMEBOL", "H", 1634.70, 74, 400, 89, 2, 15, False),
    # Group I
    ("France",                 "🇫🇷", "UEFA",     "I", 1925.86, 85, 1100, 88, 2, 17, False),
    ("Senegal",                "🇸🇳", "CAF",      "I", 1653.43, 74, 320, 90, 0, 4,  False),
    ("Iraq",                   "🇮🇶", "AFC",      "I", 1400.00, 57, 30,  88, 0, 2,  False),  # (est)
    ("Norway",                 "🇳🇴", "UEFA",     "I", 1651.29, 78, 340, 91, 0, 4,  False),
    # Group J
    ("Argentina",              "🇦🇷", "CONMEBOL", "J", 1925.15, 88, 650, 90, 3, 19, False),
    ("Algeria",                "🇩🇿", "CAF",      "J", 1576.80, 70, 200, 89, 0, 5,  False),
    ("Austria",                "🇦🇹", "UEFA",     "J", 1598.82, 73, 300, 90, 0, 8,  False),
    ("Jordan",                 "🇯🇴", "AFC",      "J", 1385.00, 63, 25,  91, 0, 1,  False),  # (est)
    # Group K
    ("Portugal",               "🇵🇹", "UEFA",     "K", 1787.85, 80, 900, 91, 0, 9,  False),
    ("DR Congo",               "🇨🇩", "CAF",      "K", 1495.48, 64, 180, 88, 0, 2,  False),
    ("Uzbekistan",             "🇺🇿", "AFC",      "K", 1409.73, 64, 45,  90, 0, 1,  False),
    ("Colombia",               "🇨🇴", "CONMEBOL", "K", 1739.89, 79, 350, 90, 0, 7,  False),
    # Group L
    ("England",                "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "UEFA",     "L", 1871.39, 78, 1400, 84, 1, 17, False),
    ("Croatia",                "🇭🇷", "UEFA",     "L", 1723.05, 70, 350, 89, 0, 7,  False),
    ("Ghana",                  "🇬🇭", "CAF",      "L", 1410.00, 55, 160, 87, 0, 5,  False),  # (est)
    ("Panama",                 "🇵🇦", "CONCACAF", "L", 1478.41, 57, 35,  90, 0, 1,  False),
]


@dataclass
class Team:
    id: int
    name: str
    flag: str
    confederation: str
    group: str
    fifa_points: float
    form: int
    squad_value_m: int
    availability: int      # 0-100 squad fitness / availability (injuries proxy)
    wc_titles: int
    wc_appearances: int
    host: bool
    fifa_rank: int = 0     # rank within the 48-team field (1 = strongest)
    sentiment: float = 0.0 # 0-100 fan positivity (social-media sentiment)
    attack: float = 0.0    # expected goals scored vs an average side
    defense: float = 0.0   # expected goals conceded vs an average side

    def to_dict(self) -> dict:
        return asdict(self)


def _derive_attack_defense(points: float, form: int) -> tuple[float, float]:
    strength = (points - 1600) / 400.0      # ~ -0.75 (weakest) .. +0.81 (strongest)
    form_adj = (form - 68) / 100.0
    attack = 1.25 + strength * 1.15 + form_adj * 0.30
    defense = 1.45 - strength * 0.85 - form_adj * 0.25
    return round(max(0.7, attack), 2), round(max(0.45, defense), 2)


def load_teams() -> list[Team]:
    teams: list[Team] = []
    for i, row in enumerate(_RAW):
        name, flag, conf, group, points, form, val, avail, titles, apps, host = row
        attack, defense = _derive_attack_defense(points, form)
        teams.append(
            Team(
                id=i + 1, name=name, flag=flag, confederation=conf, group=group,
                fifa_points=points, form=form, squad_value_m=val, availability=avail,
                wc_titles=titles, wc_appearances=apps, host=host,
                sentiment=sentiment_for(name).positivity,
                attack=attack, defense=defense,
            )
        )
    for rank, t in enumerate(sorted(teams, key=lambda x: -x.fifa_points), start=1):
        t.fifa_rank = rank
    return teams


def groups_map(teams: list[Team]) -> dict[str, list[Team]]:
    out: dict[str, list[Team]] = {}
    for t in teams:
        out.setdefault(t.group, []).append(t)
    for g in out:
        out[g].sort(key=lambda x: -x.fifa_points)
    return dict(sorted(out.items()))


if __name__ == "__main__":
    ts = load_teams()
    for g, members in groups_map(ts).items():
        print(f"Group {g}: " + ", ".join(f"{m.name}({m.fifa_points:.0f})" for m in members))
    print(f"\n{len(ts)} teams · top of field: "
          + ", ".join(t.name for t in sorted(ts, key=lambda x: x.fifa_rank)[:4]))
