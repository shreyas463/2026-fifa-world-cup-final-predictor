"""Social-media fan-sentiment provider.

Estimates public/fan sentiment for each nation from social-media chatter
(positivity, conversation volume and momentum). The interface is pluggable:

  * `CuratedSentimentProvider` (default) serves a curated, documented snapshot
    derived from fan-base size and pre-tournament expectations. It runs offline
    and deterministically, so predictions are reproducible.
  * `XApiSentimentProvider` is a stub showing exactly where to wire a live
    X / Twitter (or Reddit, news) pipeline. Live scraping needs API credentials,
    which are not available in this environment.

Sentiment feeds two places: a model feature (`sentiment_diff`) and the
`/api/sentiment` endpoint / Fan Sentiment page.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class SentimentScore:
    team: str
    positivity: float   # 0-100 — share of fan sentiment that is positive/optimistic
    buzz: float         # 0-100 — relative volume of conversation vs the field
    trend: float        # -30..+30 — momentum over the last week (rising/falling)
    sample_posts: int   # approximate number of posts analysed

    @property
    def mood(self) -> str:
        if self.positivity >= 78:
            return "euphoric"
        if self.positivity >= 68:
            return "optimistic"
        if self.positivity >= 58:
            return "cautious"
        return "anxious"

    @property
    def momentum(self) -> str:
        return "rising" if self.trend > 3 else "falling" if self.trend < -3 else "steady"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["mood"] = self.mood
        d["momentum"] = self.momentum
        return d


# Curated snapshot: (positivity, buzz, trend). Grounded in real fan-base scale
# and pre-2026 expectations; illustrative, not a live scrape. Edit freely or
# replace with a live provider (see XApiSentimentProvider).
_CURATED: dict[str, tuple[float, float, float]] = {
    "Argentina": (86, 95, 8), "Spain": (88, 82, 12), "France": (80, 88, 5),
    "England": (74, 90, -4), "Brazil": (78, 96, 3), "Portugal": (79, 80, 6),
    "Netherlands": (72, 66, 2), "Germany": (70, 78, -6), "Belgium": (63, 55, -5),
    "Croatia": (71, 45, 3), "Uruguay": (74, 52, 4), "Colombia": (80, 60, 7),
    "Morocco": (85, 70, 10), "Switzerland": (62, 40, -2), "Mexico": (75, 85, 6),
    "USA": (72, 88, 9), "Canada": (68, 60, 5), "Senegal": (73, 58, 4),
    "Japan": (79, 64, 6), "Norway": (77, 62, 8), "Iran": (66, 45, -3),
    "South Korea": (72, 66, 3), "Ecuador": (69, 48, 2), "Austria": (73, 44, 5),
    "Egypt": (70, 62, 2), "Turkey": (71, 68, 4), "Australia": (64, 46, -2),
    "Algeria": (72, 58, 5), "Ivory Coast": (70, 52, 3), "Paraguay": (62, 38, 1),
    "Sweden": (60, 50, -4), "Scotland": (66, 55, 2), "DR Congo": (68, 40, 6),
    "Panama": (58, 34, 2), "Uzbekistan": (67, 36, 9), "Saudi Arabia": (57, 55, -3),
    "Qatar": (55, 44, -2), "South Africa": (64, 48, 3), "Czech Republic": (61, 42, -2),
    "Bosnia and Herzegovina": (66, 40, 3), "Haiti": (60, 30, 2), "Curacao": (63, 26, 5),
    "New Zealand": (59, 32, 1), "Cape Verde": (72, 34, 11), "Iraq": (58, 40, -2),
    "Jordan": (64, 38, 7), "Ghana": (61, 56, -3), "Tunisia": (60, 46, -2),
}


class SentimentProvider:
    """Interface for a fan-sentiment source."""

    def score(self, team: str) -> SentimentScore:  # pragma: no cover - interface
        raise NotImplementedError

    def all(self) -> dict[str, SentimentScore]:  # pragma: no cover - interface
        raise NotImplementedError


class CuratedSentimentProvider(SentimentProvider):
    def score(self, team: str) -> SentimentScore:
        pos, buzz, trend = _CURATED.get(team, (60.0, 35.0, 0.0))
        # Volume of posts scales with buzz; deterministic, no randomness.
        posts = int(round(buzz * 1800 + 400))
        return SentimentScore(team=team, positivity=float(pos), buzz=float(buzz),
                              trend=float(trend), sample_posts=posts)

    def all(self) -> dict[str, SentimentScore]:
        return {name: self.score(name) for name in _CURATED}


class XApiSentimentProvider(SentimentProvider):
    """Live X / Twitter sentiment — wire your pipeline here.

    A real implementation would: (1) query recent posts per team hashtag via the
    X API, (2) run a sentiment classifier, (3) aggregate positivity / volume /
    trend. Requires X_BEARER_TOKEN and is intentionally not enabled offline.
    """

    def __init__(self, bearer_token: str | None = None):
        self.bearer_token = bearer_token

    def score(self, team: str) -> SentimentScore:  # pragma: no cover - stub
        raise NotImplementedError(
            "Live X sentiment requires an API bearer token. Set X_BEARER_TOKEN and "
            "implement post retrieval + a sentiment classifier, or use "
            "CuratedSentimentProvider."
        )

    def all(self) -> dict[str, SentimentScore]:  # pragma: no cover - stub
        raise NotImplementedError


_provider: SentimentProvider = CuratedSentimentProvider()


def get_provider() -> SentimentProvider:
    return _provider


def sentiment_for(team: str) -> SentimentScore:
    return _provider.score(team)


if __name__ == "__main__":
    for name, s in sorted(get_provider().all().items(), key=lambda kv: -kv[1].buzz)[:12]:
        print(f"{name:24s} pos={s.positivity:4.0f}  buzz={s.buzz:4.0f}  "
              f"{s.momentum:7s}  {s.mood}")
