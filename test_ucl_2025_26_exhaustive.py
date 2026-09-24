"""Exhaustive UEFA Champions League 2025/26 selection test.

All 189 real matches from the completed 2025/26 edition are frozen here.
No network calls or fixture discovery happen at test runtime.
"""

import json
import unittest
from pathlib import Path

from match_discovery import STAGE_RANK, load_team_config, selection_reasons

CONFIG_FILE = Path("auto_matches.json")

FIXTURES = [
    {
        "id": "ucl2526-001",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8315",
            "name": "Athletic Club"
        },
        "away": {
            "id": "9825",
            "name": "Arsenal FC"
        }
    },
    {
        "id": "ucl2526-002",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8640",
            "name": "PSV"
        },
        "away": {
            "id": "7978",
            "name": "Royale Union Saint-Gilloise"
        }
    },
    {
        "id": "ucl2526-003",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9885",
            "name": "Juventus FC"
        },
        "away": {
            "id": "9789",
            "name": "Borussia Dortmund"
        }
    },
    {
        "id": "ucl2526-004",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        },
        "away": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        }
    },
    {
        "id": "ucl2526-005",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        },
        "away": {
            "id": "10205",
            "name": "Villarreal CF"
        }
    },
    {
        "id": "ucl2526-006",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8633",
            "name": "Real Madrid CF"
        },
        "away": {
            "id": "8592",
            "name": "Olympique de Marseille"
        }
    },
    {
        "id": "ucl2526-007",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7787",
            "name": "SK Slavia Praha"
        },
        "away": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        }
    },
    {
        "id": "ucl2526-008",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        },
        "away": {
            "id": "2137",
            "name": "Paphos FC"
        }
    },
    {
        "id": "ucl2526-009",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8593",
            "name": "AFC Ajax"
        },
        "away": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        }
    },
    {
        "id": "ucl2526-010",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8650",
            "name": "Liverpool FC"
        },
        "away": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        }
    },
    {
        "id": "ucl2526-011",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        },
        "away": {
            "id": "8524",
            "name": "Atalanta BC"
        }
    },
    {
        "id": "ucl2526-012",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9823",
            "name": "FC Bayern München"
        },
        "away": {
            "id": "8455",
            "name": "Chelsea FC"
        }
    },
    {
        "id": "ucl2526-013",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8391",
            "name": "FC København"
        },
        "away": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        }
    },
    {
        "id": "ucl2526-014",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8342",
            "name": "Club Brugge KV"
        },
        "away": {
            "id": "9829",
            "name": "AS Monaco FC"
        }
    },
    {
        "id": "ucl2526-015",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "10261",
            "name": "Newcastle United FC"
        },
        "away": {
            "id": "8634",
            "name": "FC Barcelona"
        }
    },
    {
        "id": "ucl2526-016",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8456",
            "name": "Manchester City FC"
        },
        "away": {
            "id": "9875",
            "name": "SSC Napoli"
        }
    },
    {
        "id": "ucl2526-017",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9810",
            "name": "Eintracht Frankfurt"
        },
        "away": {
            "id": "8637",
            "name": "Galatasaray SK"
        }
    },
    {
        "id": "ucl2526-018",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        },
        "away": {
            "id": "8037",
            "name": "FK Kairat"
        }
    },
    {
        "id": "ucl2526-019",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8524",
            "name": "Atalanta BC"
        },
        "away": {
            "id": "8342",
            "name": "Club Brugge KV"
        }
    },
    {
        "id": "ucl2526-020",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8037",
            "name": "FK Kairat"
        },
        "away": {
            "id": "8633",
            "name": "Real Madrid CF"
        }
    },
    {
        "id": "ucl2526-021",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8637",
            "name": "Galatasaray SK"
        },
        "away": {
            "id": "8650",
            "name": "Liverpool FC"
        }
    },
    {
        "id": "ucl2526-022",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        },
        "away": {
            "id": "9810",
            "name": "Eintracht Frankfurt"
        }
    },
    {
        "id": "ucl2526-023",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8592",
            "name": "Olympique de Marseille"
        },
        "away": {
            "id": "8593",
            "name": "AFC Ajax"
        }
    },
    {
        "id": "ucl2526-024",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        },
        "away": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        }
    },
    {
        "id": "ucl2526-025",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "2137",
            "name": "Paphos FC"
        },
        "away": {
            "id": "9823",
            "name": "FC Bayern München"
        }
    },
    {
        "id": "ucl2526-026",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8455",
            "name": "Chelsea FC"
        },
        "away": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        }
    },
    {
        "id": "ucl2526-027",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        },
        "away": {
            "id": "7787",
            "name": "SK Slavia Praha"
        }
    },
    {
        "id": "ucl2526-028",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        },
        "away": {
            "id": "8391",
            "name": "FC København"
        }
    },
    {
        "id": "ucl2526-029",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7978",
            "name": "Royale Union Saint-Gilloise"
        },
        "away": {
            "id": "10261",
            "name": "Newcastle United FC"
        }
    },
    {
        "id": "ucl2526-030",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9789",
            "name": "Borussia Dortmund"
        },
        "away": {
            "id": "8315",
            "name": "Athletic Club"
        }
    },
    {
        "id": "ucl2526-031",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8634",
            "name": "FC Barcelona"
        },
        "away": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        }
    },
    {
        "id": "ucl2526-032",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9829",
            "name": "AS Monaco FC"
        },
        "away": {
            "id": "8456",
            "name": "Manchester City FC"
        }
    },
    {
        "id": "ucl2526-033",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        },
        "away": {
            "id": "8640",
            "name": "PSV"
        }
    },
    {
        "id": "ucl2526-034",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9825",
            "name": "Arsenal FC"
        },
        "away": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        }
    },
    {
        "id": "ucl2526-035",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "10205",
            "name": "Villarreal CF"
        },
        "away": {
            "id": "9885",
            "name": "Juventus FC"
        }
    },
    {
        "id": "ucl2526-036",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9875",
            "name": "SSC Napoli"
        },
        "away": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        }
    },
    {
        "id": "ucl2526-037",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8634",
            "name": "FC Barcelona"
        },
        "away": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        }
    },
    {
        "id": "ucl2526-038",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8037",
            "name": "FK Kairat"
        },
        "away": {
            "id": "2137",
            "name": "Paphos FC"
        }
    },
    {
        "id": "ucl2526-039",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7978",
            "name": "Royale Union Saint-Gilloise"
        },
        "away": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        }
    },
    {
        "id": "ucl2526-040",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8391",
            "name": "FC København"
        },
        "away": {
            "id": "9789",
            "name": "Borussia Dortmund"
        }
    },
    {
        "id": "ucl2526-041",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        },
        "away": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        }
    },
    {
        "id": "ucl2526-042",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "10205",
            "name": "Villarreal CF"
        },
        "away": {
            "id": "8456",
            "name": "Manchester City FC"
        }
    },
    {
        "id": "ucl2526-043",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9825",
            "name": "Arsenal FC"
        },
        "away": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        }
    },
    {
        "id": "ucl2526-044",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "10261",
            "name": "Newcastle United FC"
        },
        "away": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        }
    },
    {
        "id": "ucl2526-045",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8640",
            "name": "PSV"
        },
        "away": {
            "id": "9875",
            "name": "SSC Napoli"
        }
    },
    {
        "id": "ucl2526-046",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8637",
            "name": "Galatasaray SK"
        },
        "away": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        }
    },
    {
        "id": "ucl2526-047",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8315",
            "name": "Athletic Club"
        },
        "away": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        }
    },
    {
        "id": "ucl2526-048",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9810",
            "name": "Eintracht Frankfurt"
        },
        "away": {
            "id": "8650",
            "name": "Liverpool FC"
        }
    },
    {
        "id": "ucl2526-049",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8524",
            "name": "Atalanta BC"
        },
        "away": {
            "id": "7787",
            "name": "SK Slavia Praha"
        }
    },
    {
        "id": "ucl2526-050",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        },
        "away": {
            "id": "8592",
            "name": "Olympique de Marseille"
        }
    },
    {
        "id": "ucl2526-051",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9829",
            "name": "AS Monaco FC"
        },
        "away": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        }
    },
    {
        "id": "ucl2526-052",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9823",
            "name": "FC Bayern München"
        },
        "away": {
            "id": "8342",
            "name": "Club Brugge KV"
        }
    },
    {
        "id": "ucl2526-053",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8455",
            "name": "Chelsea FC"
        },
        "away": {
            "id": "8593",
            "name": "AFC Ajax"
        }
    },
    {
        "id": "ucl2526-054",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8633",
            "name": "Real Madrid CF"
        },
        "away": {
            "id": "9885",
            "name": "Juventus FC"
        }
    },
    {
        "id": "ucl2526-055",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7787",
            "name": "SK Slavia Praha"
        },
        "away": {
            "id": "9825",
            "name": "Arsenal FC"
        }
    },
    {
        "id": "ucl2526-056",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9875",
            "name": "SSC Napoli"
        },
        "away": {
            "id": "9810",
            "name": "Eintracht Frankfurt"
        }
    },
    {
        "id": "ucl2526-057",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9885",
            "name": "Juventus FC"
        },
        "away": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        }
    },
    {
        "id": "ucl2526-058",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        },
        "away": {
            "id": "7978",
            "name": "Royale Union Saint-Gilloise"
        }
    },
    {
        "id": "ucl2526-059",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        },
        "away": {
            "id": "8391",
            "name": "FC København"
        }
    },
    {
        "id": "ucl2526-060",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        },
        "away": {
            "id": "9829",
            "name": "AS Monaco FC"
        }
    },
    {
        "id": "ucl2526-061",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        },
        "away": {
            "id": "8640",
            "name": "PSV"
        }
    },
    {
        "id": "ucl2526-062",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        },
        "away": {
            "id": "9823",
            "name": "FC Bayern München"
        }
    },
    {
        "id": "ucl2526-063",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8650",
            "name": "Liverpool FC"
        },
        "away": {
            "id": "8633",
            "name": "Real Madrid CF"
        }
    },
    {
        "id": "ucl2526-064",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "2137",
            "name": "Paphos FC"
        },
        "away": {
            "id": "10205",
            "name": "Villarreal CF"
        }
    },
    {
        "id": "ucl2526-065",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        },
        "away": {
            "id": "8455",
            "name": "Chelsea FC"
        }
    },
    {
        "id": "ucl2526-066",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        },
        "away": {
            "id": "8037",
            "name": "FK Kairat"
        }
    },
    {
        "id": "ucl2526-067",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8456",
            "name": "Manchester City FC"
        },
        "away": {
            "id": "9789",
            "name": "Borussia Dortmund"
        }
    },
    {
        "id": "ucl2526-068",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8342",
            "name": "Club Brugge KV"
        },
        "away": {
            "id": "8634",
            "name": "FC Barcelona"
        }
    },
    {
        "id": "ucl2526-069",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        },
        "away": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        }
    },
    {
        "id": "ucl2526-070",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8592",
            "name": "Olympique de Marseille"
        },
        "away": {
            "id": "8524",
            "name": "Atalanta BC"
        }
    },
    {
        "id": "ucl2526-071",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8593",
            "name": "AFC Ajax"
        },
        "away": {
            "id": "8637",
            "name": "Galatasaray SK"
        }
    },
    {
        "id": "ucl2526-072",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "10261",
            "name": "Newcastle United FC"
        },
        "away": {
            "id": "8315",
            "name": "Athletic Club"
        }
    },
    {
        "id": "ucl2526-073",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8593",
            "name": "AFC Ajax"
        },
        "away": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        }
    },
    {
        "id": "ucl2526-074",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8637",
            "name": "Galatasaray SK"
        },
        "away": {
            "id": "7978",
            "name": "Royale Union Saint-Gilloise"
        }
    },
    {
        "id": "ucl2526-075",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9789",
            "name": "Borussia Dortmund"
        },
        "away": {
            "id": "10205",
            "name": "Villarreal CF"
        }
    },
    {
        "id": "ucl2526-076",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8456",
            "name": "Manchester City FC"
        },
        "away": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        }
    },
    {
        "id": "ucl2526-077",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        },
        "away": {
            "id": "9885",
            "name": "Juventus FC"
        }
    },
    {
        "id": "ucl2526-078",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8592",
            "name": "Olympique de Marseille"
        },
        "away": {
            "id": "10261",
            "name": "Newcastle United FC"
        }
    },
    {
        "id": "ucl2526-079",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7787",
            "name": "SK Slavia Praha"
        },
        "away": {
            "id": "8315",
            "name": "Athletic Club"
        }
    },
    {
        "id": "ucl2526-080",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9875",
            "name": "SSC Napoli"
        },
        "away": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        }
    },
    {
        "id": "ucl2526-081",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8455",
            "name": "Chelsea FC"
        },
        "away": {
            "id": "8634",
            "name": "FC Barcelona"
        }
    },
    {
        "id": "ucl2526-082",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "2137",
            "name": "Paphos FC"
        },
        "away": {
            "id": "9829",
            "name": "AS Monaco FC"
        }
    },
    {
        "id": "ucl2526-083",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8391",
            "name": "FC København"
        },
        "away": {
            "id": "8037",
            "name": "FK Kairat"
        }
    },
    {
        "id": "ucl2526-084",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8650",
            "name": "Liverpool FC"
        },
        "away": {
            "id": "8640",
            "name": "PSV"
        }
    },
    {
        "id": "ucl2526-085",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        },
        "away": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        }
    },
    {
        "id": "ucl2526-086",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9810",
            "name": "Eintracht Frankfurt"
        },
        "away": {
            "id": "8524",
            "name": "Atalanta BC"
        }
    },
    {
        "id": "ucl2526-087",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        },
        "away": {
            "id": "8342",
            "name": "Club Brugge KV"
        }
    },
    {
        "id": "ucl2526-088",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9825",
            "name": "Arsenal FC"
        },
        "away": {
            "id": "9823",
            "name": "FC Bayern München"
        }
    },
    {
        "id": "ucl2526-089",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        },
        "away": {
            "id": "8633",
            "name": "Real Madrid CF"
        }
    },
    {
        "id": "ucl2526-090",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        },
        "away": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        }
    },
    {
        "id": "ucl2526-091",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8037",
            "name": "FK Kairat"
        },
        "away": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        }
    },
    {
        "id": "ucl2526-092",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9823",
            "name": "FC Bayern München"
        },
        "away": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        }
    },
    {
        "id": "ucl2526-093",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8634",
            "name": "FC Barcelona"
        },
        "away": {
            "id": "9810",
            "name": "Eintracht Frankfurt"
        }
    },
    {
        "id": "ucl2526-094",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8640",
            "name": "PSV"
        },
        "away": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        }
    },
    {
        "id": "ucl2526-095",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7978",
            "name": "Royale Union Saint-Gilloise"
        },
        "away": {
            "id": "8592",
            "name": "Olympique de Marseille"
        }
    },
    {
        "id": "ucl2526-096",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        },
        "away": {
            "id": "7787",
            "name": "SK Slavia Praha"
        }
    },
    {
        "id": "ucl2526-097",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9829",
            "name": "AS Monaco FC"
        },
        "away": {
            "id": "8637",
            "name": "Galatasaray SK"
        }
    },
    {
        "id": "ucl2526-098",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8524",
            "name": "Atalanta BC"
        },
        "away": {
            "id": "8455",
            "name": "Chelsea FC"
        }
    },
    {
        "id": "ucl2526-099",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        },
        "away": {
            "id": "8650",
            "name": "Liverpool FC"
        }
    },
    {
        "id": "ucl2526-100",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "10205",
            "name": "Villarreal CF"
        },
        "away": {
            "id": "8391",
            "name": "FC København"
        }
    },
    {
        "id": "ucl2526-101",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        },
        "away": {
            "id": "8593",
            "name": "AFC Ajax"
        }
    },
    {
        "id": "ucl2526-102",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9789",
            "name": "Borussia Dortmund"
        },
        "away": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        }
    },
    {
        "id": "ucl2526-103",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8315",
            "name": "Athletic Club"
        },
        "away": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        }
    },
    {
        "id": "ucl2526-104",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        },
        "away": {
            "id": "10261",
            "name": "Newcastle United FC"
        }
    },
    {
        "id": "ucl2526-105",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8342",
            "name": "Club Brugge KV"
        },
        "away": {
            "id": "9825",
            "name": "Arsenal FC"
        }
    },
    {
        "id": "ucl2526-106",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        },
        "away": {
            "id": "9875",
            "name": "SSC Napoli"
        }
    },
    {
        "id": "ucl2526-107",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9885",
            "name": "Juventus FC"
        },
        "away": {
            "id": "2137",
            "name": "Paphos FC"
        }
    },
    {
        "id": "ucl2526-108",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8633",
            "name": "Real Madrid CF"
        },
        "away": {
            "id": "8456",
            "name": "Manchester City FC"
        }
    },
    {
        "id": "ucl2526-109",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8037",
            "name": "FK Kairat"
        },
        "away": {
            "id": "8342",
            "name": "Club Brugge KV"
        }
    },
    {
        "id": "ucl2526-110",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        },
        "away": {
            "id": "8456",
            "name": "Manchester City FC"
        }
    },
    {
        "id": "ucl2526-111",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        },
        "away": {
            "id": "9789",
            "name": "Borussia Dortmund"
        }
    },
    {
        "id": "ucl2526-112",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        },
        "away": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        }
    },
    {
        "id": "ucl2526-113",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        },
        "away": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        }
    },
    {
        "id": "ucl2526-114",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "10205",
            "name": "Villarreal CF"
        },
        "away": {
            "id": "8593",
            "name": "AFC Ajax"
        }
    },
    {
        "id": "ucl2526-115",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8391",
            "name": "FC København"
        },
        "away": {
            "id": "9875",
            "name": "SSC Napoli"
        }
    },
    {
        "id": "ucl2526-116",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8633",
            "name": "Real Madrid CF"
        },
        "away": {
            "id": "9829",
            "name": "AS Monaco FC"
        }
    },
    {
        "id": "ucl2526-117",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        },
        "away": {
            "id": "9825",
            "name": "Arsenal FC"
        }
    },
    {
        "id": "ucl2526-118",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        },
        "away": {
            "id": "9810",
            "name": "Eintracht Frankfurt"
        }
    },
    {
        "id": "ucl2526-119",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8637",
            "name": "Galatasaray SK"
        },
        "away": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        }
    },
    {
        "id": "ucl2526-120",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8592",
            "name": "Olympique de Marseille"
        },
        "away": {
            "id": "8650",
            "name": "Liverpool FC"
        }
    },
    {
        "id": "ucl2526-121",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7787",
            "name": "SK Slavia Praha"
        },
        "away": {
            "id": "8634",
            "name": "FC Barcelona"
        }
    },
    {
        "id": "ucl2526-122",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8524",
            "name": "Atalanta BC"
        },
        "away": {
            "id": "8315",
            "name": "Athletic Club"
        }
    },
    {
        "id": "ucl2526-123",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9885",
            "name": "Juventus FC"
        },
        "away": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        }
    },
    {
        "id": "ucl2526-124",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "10261",
            "name": "Newcastle United FC"
        },
        "away": {
            "id": "8640",
            "name": "PSV"
        }
    },
    {
        "id": "ucl2526-125",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9823",
            "name": "FC Bayern München"
        },
        "away": {
            "id": "7978",
            "name": "Royale Union Saint-Gilloise"
        }
    },
    {
        "id": "ucl2526-126",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8455",
            "name": "Chelsea FC"
        },
        "away": {
            "id": "2137",
            "name": "Paphos FC"
        }
    },
    {
        "id": "ucl2526-127",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8650",
            "name": "Liverpool FC"
        },
        "away": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        }
    },
    {
        "id": "ucl2526-128",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8634",
            "name": "FC Barcelona"
        },
        "away": {
            "id": "8391",
            "name": "FC København"
        }
    },
    {
        "id": "ucl2526-129",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8456",
            "name": "Manchester City FC"
        },
        "away": {
            "id": "8637",
            "name": "Galatasaray SK"
        }
    },
    {
        "id": "ucl2526-130",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        },
        "away": {
            "id": "10205",
            "name": "Villarreal CF"
        }
    },
    {
        "id": "ucl2526-131",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9825",
            "name": "Arsenal FC"
        },
        "away": {
            "id": "8037",
            "name": "FK Kairat"
        }
    },
    {
        "id": "ucl2526-132",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "7978",
            "name": "Royale Union Saint-Gilloise"
        },
        "away": {
            "id": "8524",
            "name": "Atalanta BC"
        }
    },
    {
        "id": "ucl2526-133",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8342",
            "name": "Club Brugge KV"
        },
        "away": {
            "id": "8592",
            "name": "Olympique de Marseille"
        }
    },
    {
        "id": "ucl2526-134",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9810",
            "name": "Eintracht Frankfurt"
        },
        "away": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        }
    },
    {
        "id": "ucl2526-135",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9829",
            "name": "AS Monaco FC"
        },
        "away": {
            "id": "9885",
            "name": "Juventus FC"
        }
    },
    {
        "id": "ucl2526-136",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        },
        "away": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        }
    },
    {
        "id": "ucl2526-137",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8315",
            "name": "Athletic Club"
        },
        "away": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        }
    },
    {
        "id": "ucl2526-138",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8593",
            "name": "AFC Ajax"
        },
        "away": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        }
    },
    {
        "id": "ucl2526-139",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        },
        "away": {
            "id": "10261",
            "name": "Newcastle United FC"
        }
    },
    {
        "id": "ucl2526-140",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "2137",
            "name": "Paphos FC"
        },
        "away": {
            "id": "7787",
            "name": "SK Slavia Praha"
        }
    },
    {
        "id": "ucl2526-141",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "8640",
            "name": "PSV"
        },
        "away": {
            "id": "9823",
            "name": "FC Bayern München"
        }
    },
    {
        "id": "ucl2526-142",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9875",
            "name": "SSC Napoli"
        },
        "away": {
            "id": "8455",
            "name": "Chelsea FC"
        }
    },
    {
        "id": "ucl2526-143",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        },
        "away": {
            "id": "8633",
            "name": "Real Madrid CF"
        }
    },
    {
        "id": "ucl2526-144",
        "leagueId": "45",
        "stage": "league_phase",
        "home": {
            "id": "9789",
            "name": "Borussia Dortmund"
        },
        "away": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        }
    },
    {
        "id": "ucl2526-145",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "8637",
            "name": "Galatasaray SK"
        },
        "away": {
            "id": "9885",
            "name": "Juventus FC"
        }
    },
    {
        "id": "ucl2526-146",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        },
        "away": {
            "id": "8633",
            "name": "Real Madrid CF"
        }
    },
    {
        "id": "ucl2526-147",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "9829",
            "name": "AS Monaco FC"
        },
        "away": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        }
    },
    {
        "id": "ucl2526-148",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "9789",
            "name": "Borussia Dortmund"
        },
        "away": {
            "id": "8524",
            "name": "Atalanta BC"
        }
    },
    {
        "id": "ucl2526-149",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        },
        "away": {
            "id": "10261",
            "name": "Newcastle United FC"
        }
    },
    {
        "id": "ucl2526-150",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "8342",
            "name": "Club Brugge KV"
        },
        "away": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        }
    },
    {
        "id": "ucl2526-151",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        },
        "away": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        }
    },
    {
        "id": "ucl2526-152",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        },
        "away": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        }
    },
    {
        "id": "ucl2526-153",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        },
        "away": {
            "id": "8342",
            "name": "Club Brugge KV"
        }
    },
    {
        "id": "ucl2526-154",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "10261",
            "name": "Newcastle United FC"
        },
        "away": {
            "id": "7981",
            "name": "Qarabağ Ağdam FK"
        }
    },
    {
        "id": "ucl2526-155",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        },
        "away": {
            "id": "8638",
            "name": "PAE Olympiakos SFP"
        }
    },
    {
        "id": "ucl2526-156",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "8636",
            "name": "FC Internazionale Milano"
        },
        "away": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        }
    },
    {
        "id": "ucl2526-157",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "8524",
            "name": "Atalanta BC"
        },
        "away": {
            "id": "9789",
            "name": "Borussia Dortmund"
        }
    },
    {
        "id": "ucl2526-158",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "8633",
            "name": "Real Madrid CF"
        },
        "away": {
            "id": "9772",
            "name": "Sport Lisboa e Benfica"
        }
    },
    {
        "id": "ucl2526-159",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        },
        "away": {
            "id": "9829",
            "name": "AS Monaco FC"
        }
    },
    {
        "id": "ucl2526-160",
        "leagueId": "45",
        "stage": "playoff",
        "home": {
            "id": "9885",
            "name": "Juventus FC"
        },
        "away": {
            "id": "8637",
            "name": "Galatasaray SK"
        }
    },
    {
        "id": "ucl2526-161",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8637",
            "name": "Galatasaray SK"
        },
        "away": {
            "id": "8650",
            "name": "Liverpool FC"
        }
    },
    {
        "id": "ucl2526-162",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8524",
            "name": "Atalanta BC"
        },
        "away": {
            "id": "9823",
            "name": "FC Bayern München"
        }
    },
    {
        "id": "ucl2526-163",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "10261",
            "name": "Newcastle United FC"
        },
        "away": {
            "id": "8634",
            "name": "FC Barcelona"
        }
    },
    {
        "id": "ucl2526-164",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        },
        "away": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        }
    },
    {
        "id": "ucl2526-165",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        },
        "away": {
            "id": "9825",
            "name": "Arsenal FC"
        }
    },
    {
        "id": "ucl2526-166",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        },
        "away": {
            "id": "8455",
            "name": "Chelsea FC"
        }
    },
    {
        "id": "ucl2526-167",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8633",
            "name": "Real Madrid CF"
        },
        "away": {
            "id": "8456",
            "name": "Manchester City FC"
        }
    },
    {
        "id": "ucl2526-168",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        },
        "away": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        }
    },
    {
        "id": "ucl2526-169",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        },
        "away": {
            "id": "8402",
            "name": "FK Bodø/Glimt"
        }
    },
    {
        "id": "ucl2526-170",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8455",
            "name": "Chelsea FC"
        },
        "away": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        }
    },
    {
        "id": "ucl2526-171",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8456",
            "name": "Manchester City FC"
        },
        "away": {
            "id": "8633",
            "name": "Real Madrid CF"
        }
    },
    {
        "id": "ucl2526-172",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "9825",
            "name": "Arsenal FC"
        },
        "away": {
            "id": "8178",
            "name": "Bayer 04 Leverkusen"
        }
    },
    {
        "id": "ucl2526-173",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8634",
            "name": "FC Barcelona"
        },
        "away": {
            "id": "10261",
            "name": "Newcastle United FC"
        }
    },
    {
        "id": "ucl2526-174",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8650",
            "name": "Liverpool FC"
        },
        "away": {
            "id": "8637",
            "name": "Galatasaray SK"
        }
    },
    {
        "id": "ucl2526-175",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "9823",
            "name": "FC Bayern München"
        },
        "away": {
            "id": "8524",
            "name": "Atalanta BC"
        }
    },
    {
        "id": "ucl2526-176",
        "leagueId": "45",
        "stage": "round_of_16",
        "home": {
            "id": "8586",
            "name": "Tottenham Hotspur FC"
        },
        "away": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        }
    },
    {
        "id": "ucl2526-177",
        "leagueId": "45",
        "stage": "quarter_final",
        "home": {
            "id": "8633",
            "name": "Real Madrid CF"
        },
        "away": {
            "id": "9823",
            "name": "FC Bayern München"
        }
    },
    {
        "id": "ucl2526-178",
        "leagueId": "45",
        "stage": "quarter_final",
        "home": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        },
        "away": {
            "id": "9825",
            "name": "Arsenal FC"
        }
    },
    {
        "id": "ucl2526-179",
        "leagueId": "45",
        "stage": "quarter_final",
        "home": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        },
        "away": {
            "id": "8650",
            "name": "Liverpool FC"
        }
    },
    {
        "id": "ucl2526-180",
        "leagueId": "45",
        "stage": "quarter_final",
        "home": {
            "id": "8634",
            "name": "FC Barcelona"
        },
        "away": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        }
    },
    {
        "id": "ucl2526-181",
        "leagueId": "45",
        "stage": "quarter_final",
        "home": {
            "id": "8650",
            "name": "Liverpool FC"
        },
        "away": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        }
    },
    {
        "id": "ucl2526-182",
        "leagueId": "45",
        "stage": "quarter_final",
        "home": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        },
        "away": {
            "id": "8634",
            "name": "FC Barcelona"
        }
    },
    {
        "id": "ucl2526-183",
        "leagueId": "45",
        "stage": "quarter_final",
        "home": {
            "id": "9823",
            "name": "FC Bayern München"
        },
        "away": {
            "id": "8633",
            "name": "Real Madrid CF"
        }
    },
    {
        "id": "ucl2526-184",
        "leagueId": "45",
        "stage": "quarter_final",
        "home": {
            "id": "9825",
            "name": "Arsenal FC"
        },
        "away": {
            "id": "9768",
            "name": "Sporting Clube de Portugal"
        }
    },
    {
        "id": "ucl2526-185",
        "leagueId": "45",
        "stage": "semi_final",
        "home": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        },
        "away": {
            "id": "9823",
            "name": "FC Bayern München"
        }
    },
    {
        "id": "ucl2526-186",
        "leagueId": "45",
        "stage": "semi_final",
        "home": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        },
        "away": {
            "id": "9825",
            "name": "Arsenal FC"
        }
    },
    {
        "id": "ucl2526-187",
        "leagueId": "45",
        "stage": "semi_final",
        "home": {
            "id": "9825",
            "name": "Arsenal FC"
        },
        "away": {
            "id": "9906",
            "name": "Club Atlético de Madrid"
        }
    },
    {
        "id": "ucl2526-188",
        "leagueId": "45",
        "stage": "semi_final",
        "home": {
            "id": "9823",
            "name": "FC Bayern München"
        },
        "away": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        }
    },
    {
        "id": "ucl2526-189",
        "leagueId": "45",
        "stage": "final",
        "home": {
            "id": "9847",
            "name": "Paris Saint-Germain FC"
        },
        "away": {
            "id": "9825",
            "name": "Arsenal FC"
        }
    }
]


class ChampionsLeague202526ExhaustiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        cls.rule = next(
            rule for rule in cls.config["competitions"]
            if str(rule.get("id")) == "45"
        )
        cls.selected_team_ids = {
            str(value) for value in cls.config.get("team_ids", [])
        }
        cls.by_name, cls.by_country = load_team_config()

    def test_all_189_fixtures_are_present_and_decided(self):
        self.assertEqual(len(FIXTURES), 189)
        self.assertEqual(len({f["id"] for f in FIXTURES}), 189)

        rule_selected = 0
        rule_rejected = 0
        production_selected = 0

        for index, fixture in enumerate(FIXTURES, 1):
            self.assertEqual(str(fixture["leagueId"]), "45")
            self.assertIn(fixture["stage"], STAGE_RANK)

            rule_reasons = selection_reasons(
                fixture, {"competitions": [self.rule]}, set(),
                self.by_name, self.by_country,
            )
            production_reasons = selection_reasons(
                fixture, self.config, self.selected_team_ids,
                self.by_name, self.by_country,
            )

            if rule_reasons:
                rule_selected += 1
            else:
                rule_rejected += 1
            if production_reasons:
                production_selected += 1

            print(
                f"{index:03d}. {fixture['id']} | {fixture['stage']:<14} | "
                f"{fixture['home']['name']} vs {fixture['away']['name']} | "
                f"RULE={'SELECTED' if rule_reasons else 'REJECTED':<8} | "
                f"reason: {', '.join(rule_reasons) if rule_reasons else 'no matching competition rule'}"
            )
            print(
                f"     PRODUCTION={'SELECTED' if production_reasons else 'REJECTED':<8} | "
                f"reason: {', '.join(production_reasons) if production_reasons else 'no matching rule'}"
            )

        print("-" * 110)
        print(
            f"UCL 2025/26 | {len(FIXTURES)} matches | "
            f"competition-rule selected={rule_selected} | "
            f"rejected={rule_rejected} | "
            f"full-production selected={production_selected}"
        )

        expected = [
            f for f in FIXTURES
            if f["stage"] in {"round_of_16", "quarter_final", "semi_final", "final"}
        ]
        self.assertEqual(len(expected), 29)
        self.assertEqual(rule_selected, 29)
        self.assertEqual(rule_rejected, 160)

        for fixture in expected:
            reasons = selection_reasons(
                fixture, {"competitions": [self.rule]}, set(),
                self.by_name, self.by_country,
            )
            self.assertTrue(reasons)

        for fixture in FIXTURES:
            if fixture["stage"] not in {
                "round_of_16", "quarter_final", "semi_final", "final"
            }:
                reasons = selection_reasons(
                    fixture, {"competitions": [self.rule]}, set(),
                    self.by_name, self.by_country,
                )
                self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
