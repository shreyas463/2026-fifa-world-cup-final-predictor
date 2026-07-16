"""Curated 2026 FIFA World Cup field (48 teams) and deterministic group draw.

Live match scraping is not available in this offline build, so this module
ships a curated snapshot of the projected 48-team field with realistic
strength attributes (Elo, recent form, World Cup pedigree, squad value).
All downstream features, models and simulations derive from this data, so it
is the single source of truth for team strength.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Optional

# name, flag, confederation, elo, form(0-100), squad_value_m, wc_titles, wc_apps, host
_RAW = [
    ("Argentina",     "🇦🇷", "CONMEBOL", 2085, 88, 700,  3, 18, False),
    ("France",        "🇫🇷", "UEFA",     2075, 84, 1100, 2, 16, False),
    ("Spain",         "🇪🇸", "UEFA",     2065, 90, 1000, 1, 16, False),
    ("Brazil",        "🇧🇷", "CONMEBOL", 2020, 80, 900,  5, 22, False),
    ("England",       "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "UEFA",     2000, 78, 1400, 1, 16, False),
    ("Portugal",      "🇵🇹", "UEFA",     1990, 82, 900,  0, 8,  False),
    ("Netherlands",   "🇳🇱", "UEFA",     1980, 79, 700,  0, 11, False),
    ("Germany",       "🇩🇪", "UEFA",     1965, 76, 900,  4, 20, False),
    ("Belgium",       "🇧🇪", "UEFA",     1950, 70, 500,  0, 14, False),
    ("Italy",         "🇮🇹", "UEFA",     1940, 74, 650,  4, 18, False),
    ("Croatia",       "🇭🇷", "UEFA",     1900, 72, 380,  0, 6,  False),
    ("Uruguay",       "🇺🇾", "CONMEBOL", 1895, 77, 420,  2, 14, False),
    ("Colombia",      "🇨🇴", "CONMEBOL", 1885, 81, 360,  0, 6,  False),
    ("Morocco",       "🇲🇦", "CAF",      1875, 83, 300,  0, 6,  False),
    ("Switzerland",   "🇨🇭", "UEFA",     1850, 68, 300,  0, 12, False),
    ("Denmark",       "🇩🇰", "UEFA",     1845, 71, 320,  0, 6,  False),
    ("Norway",        "🇳🇴", "UEFA",     1830, 78, 340,  0, 3,  False),
    ("Senegal",       "🇸🇳", "CAF",      1815, 73, 320,  0, 3,  False),
    ("Japan",         "🇯🇵", "AFC",      1810, 80, 260,  0, 7,  False),
    ("Serbia",        "🇷🇸", "UEFA",     1805, 67, 300,  0, 13, False),
    ("Iran",          "🇮🇷", "AFC",      1788, 69, 60,   0, 6,  False),
    ("South Korea",   "🇰🇷", "AFC",      1785, 72, 180,  0, 11, False),
    ("Ecuador",       "🇪🇨", "CONMEBOL", 1780, 70, 200,  0, 4,  False),
    ("Ukraine",       "🇺🇦", "UEFA",     1775, 64, 220,  0, 1,  False),
    ("Poland",        "🇵🇱", "UEFA",     1770, 60, 260,  0, 9,  False),
    ("Nigeria",       "🇳🇬", "CAF",      1765, 66, 240,  0, 6,  False),
    ("Algeria",       "🇩🇿", "CAF",      1760, 70, 200,  0, 4,  False),
    ("Scotland",      "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "UEFA",     1760, 66, 190,  0, 8,  False),
    ("Mexico",        "🇲🇽", "CONCACAF", 1800, 66, 210,  0, 17, True),
    ("Egypt",         "🇪🇬", "CAF",      1755, 68, 160,  0, 3,  False),
    ("Greece",        "🇬🇷", "UEFA",     1750, 69, 180,  0, 3,  False),
    ("Ivory Coast",   "🇨🇮", "CAF",      1745, 67, 260,  0, 3,  False),
    ("Paraguay",      "🇵🇾", "CONMEBOL", 1740, 63, 120,  0, 8,  False),
    ("Cameroon",      "🇨🇲", "CAF",      1735, 62, 200,  0, 8,  False),
    ("Australia",     "🇦🇺", "AFC",      1720, 63, 90,   0, 6,  False),
    ("Tunisia",       "🇹🇳", "CAF",      1710, 60, 60,   0, 6,  False),
    ("Ghana",         "🇬🇭", "CAF",      1700, 55, 160,  0, 8,  False),
    ("USA",           "🇺🇸", "CONCACAF", 1790, 69, 250,  0, 11, True),
    ("Turkey",        "🇹🇷", "UEFA",     1798, 71, 320,  0, 6,  False),
    ("Austria",       "🇦🇹", "UEFA",     1795, 75, 280,  0, 8,  False),
    ("Canada",        "🇨🇦", "CONCACAF", 1760, 65, 150,  0, 2,  True),
    ("Qatar",         "🇶🇦", "AFC",      1690, 61, 40,   0, 1,  False),
    ("Saudi Arabia",  "🇸🇦", "AFC",      1680, 58, 40,   0, 6,  False),
    ("Uzbekistan",    "🇺🇿", "AFC",      1670, 64, 45,   0, 0,  False),
    ("Costa Rica",    "🇨🇷", "CONCACAF", 1660, 54, 40,   0, 6,  False),
    ("Iraq",          "🇮🇶", "AFC",      1655, 56, 30,   0, 0,  False),
    ("Panama",        "🇵🇦", "CONCACAF", 1650, 57, 35,   0, 1,  False),
    ("New Zealand",   "🇳🇿", "OFC",      1600, 59, 30,   0, 2,  False),
]


@dataclass
class Team:
    id: int
    name: str
    flag: str
    confederation: str
    elo: int
    form: int
    squad_value_m: int
    wc_titles: int
    wc_appearances: int
    host: bool
    fifa_rank: int = 0
    group: str = ""
    attack: float = 0.0   # expected goals scored vs an average side
    defense: float = 0.0  # expected goals conceded vs an average side

    def to_dict(self) -> dict:
        return asdict(self)


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-")


def _derive_attack_defense(elo: int, form: int) -> tuple[float, float]:
    """Map strength (Elo) and current form onto attacking / defensive rates.

    Rates are expressed as goals per match against a league-average opponent,
    and are later combined multiplicatively in the Poisson match engine.
    """
    strength = (elo - 1600) / 500.0  # ~0 for weakest, ~1 for strongest
    form_adj = (form - 68) / 100.0
    attack = 1.05 + strength * 1.35 + form_adj * 0.30
    defense = 1.55 - strength * 0.95 - form_adj * 0.25
    return round(max(0.7, attack), 2), round(max(0.45, defense), 2)


def load_teams() -> list[Team]:
    """Return the 48 teams with computed fifa_rank, attack/defense and group."""
    teams: list[Team] = []
    for i, (name, flag, conf, elo, form, val, titles, apps, host) in enumerate(_RAW):
        attack, defense = _derive_attack_defense(elo, form)
        teams.append(
            Team(
                id=i + 1,
                name=name,
                flag=flag,
                confederation=conf,
                elo=elo,
                form=form,
                squad_value_m=val,
                wc_titles=titles,
                wc_appearances=apps,
                host=host,
                attack=attack,
                defense=defense,
            )
        )

    # FIFA rank derived from Elo ordering (1 = strongest)
    for rank, t in enumerate(sorted(teams, key=lambda x: -x.elo), start=1):
        t.fifa_rank = rank

    _assign_groups(teams)
    return teams


def _assign_groups(teams: list[Team]) -> None:
    """Deterministic pot-based snake draft into 12 groups (A..L) of 4.

    Hosts are seeded as group heads (Pot 1), mirroring FIFA's real procedure;
    the rest of Pot 1 and Pots 2-4 are filled by Elo. Deterministic so the
    bracket and simulations are reproducible across runs.
    """
    groups = [chr(ord("A") + i) for i in range(12)]
    by_elo = sorted(teams, key=lambda x: -x.elo)
    hosts = [t for t in by_elo if t.host]
    non_hosts = [t for t in by_elo if not t.host]

    pot1 = hosts + non_hosts[: 12 - len(hosts)]
    rest = non_hosts[12 - len(hosts):]
    pot2, pot3, pot4 = rest[:12], rest[12:24], rest[24:36]

    # Assign each pot across the 12 groups; snake the direction each pot for balance.
    for pot_index, pot in enumerate([pot1, pot2, pot3, pot4]):
        order = groups if pot_index % 2 == 0 else list(reversed(groups))
        for g, team in zip(order, pot):
            team.group = g


def groups_map(teams: list[Team]) -> dict[str, list[Team]]:
    out: dict[str, list[Team]] = {}
    for t in teams:
        out.setdefault(t.group, []).append(t)
    for g in out:
        out[g].sort(key=lambda x: -x.elo)
    return dict(sorted(out.items()))


if __name__ == "__main__":
    ts = load_teams()
    gm = groups_map(ts)
    for g, members in gm.items():
        print(f"Group {g}: " + ", ".join(f"{m.name}({m.elo})" for m in members))
    print(f"\n{len(ts)} teams, {len(gm)} groups")
