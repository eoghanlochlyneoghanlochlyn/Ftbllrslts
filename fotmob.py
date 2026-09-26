import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

from competition_translations import (
    get_persian_competition_name,
)

import team_translations as _team_translations

from team_translations import (
    get_persian_team_name,
)


# =========================================================
# تنظیمات
# =========================================================

IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")

FOTMOB_BASE_URL = "https://www.fotmob.com"

FOTMOB_API_URL = (
    "https://www.fotmob.com/api/data/matchDetails"
)

FOTMOB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "application/json,text/plain,*/*"
    ),
    "Accept-Language": (
        "en-US,en;q=0.9"
    ),
    "Referer": (
        "https://www.fotmob.com/"
    ),
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


# =========================================================
# ابزارهای عمومی
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, (int, float)):
        return str(value)

    if not isinstance(value, str):
        return str(value)

    value = re.sub(
        r"<[^>]+>",
        "",
        value,
    )

    value = (
        value
        .replace("\xa0", " ")
        .replace("\u200b", "")
        .replace("\r", " ")
        .replace("\n", " ")
    )

    return " ".join(
        value.split()
    ).strip()


def get_nested(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


def recursive_find(data, target_keys):
    if not isinstance(
        target_keys,
        (list, tuple, set),
    ):
        target_keys = {target_keys}

    if isinstance(data, dict):

        for key, value in data.items():

            if key in target_keys:
                if value is not None:
                    return value

        for value in data.values():

            result = recursive_find(
                value,
                target_keys,
            )

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:

            result = recursive_find(
                item,
                target_keys,
            )

            if result is not None:
                return result

    return None


def find_section(data, section_name):
    if not isinstance(data, dict):
        return None

    if section_name in data:
        return data[section_name]

    return recursive_find(
        data,
        {section_name},
    )


# =========================================================
# Match ID
# =========================================================

def extract_match_id(value):

    if value is None:
        return None

    if isinstance(value, int):
        return str(value)

    value = str(value).strip()

    if value.isdigit():
        return value

    patterns = [
        r"[#/]([0-9]{5,})",
        r"match(?:Id)?[=/]([0-9]{5,})",
        r"([0-9]{5,})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            value,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


# =========================================================
# دریافت API
# =========================================================

def fetch_match_api(match_id):

    match_id = extract_match_id(match_id)

    if not match_id:
        return None

    try:

        response = requests.get(
            FOTMOB_API_URL,
            params={
                "matchId": match_id,
            },
            headers=FOTMOB_HEADERS,
            timeout=30,
        )

        print(
            f"FotMob {match_id}: "
            f"API HTTP {response.status_code}"
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if not isinstance(data, dict):
            print(f"FotMob {match_id}: API returned non-object JSON; HTML backup.")
            return None

        content = data.get("content")
        header = data.get("header")
        general = data.get("general")
        if not isinstance(content, dict) or not (
            isinstance(header, dict) or isinstance(general, dict)
        ):
            print(f"FotMob {match_id}: incomplete API payload; HTML backup.")
            return None

        print(
            f"FotMob {match_id}: API PRIMARY OK | "
            f"cache={response.headers.get('Cache-Control', 'unknown')} | "
            f"bytes={len(response.content)}"
        )
        return data

    except Exception as error:

        print(
            f"FotMob {match_id}: "
            f"API error: {error}"
        )

        return None


# =========================================================
# دریافت صفحه
# =========================================================

def fetch_match_page(match_id):

    match_id = extract_match_id(match_id)

    if not match_id:
        return None

    url = (
        f"{FOTMOB_BASE_URL}/match/"
        f"{match_id}"
    )

    try:

        response = requests.get(
            url,
            headers=FOTMOB_HEADERS,
            timeout=30,
        )

        print(
            f"FotMob {match_id}: "
            f"Page HTTP {response.status_code}"
        )

        print(
            f"FotMob {match_id}: "
            f"Final URL = {response.url}"
        )

        print(
            f"FotMob {match_id}: "
            f"Response length = "
            f"{len(response.text)}"
        )

        if response.status_code != 200:
            return None

        return response.text

    except Exception as error:

        print(
            f"FotMob {match_id}: "
            f"Page error: {error}"
        )

        return None


# =========================================================
# __NEXT_DATA__
# =========================================================

def extract_next_data(html):

    if not html:
        return None

    pattern = (
        r'<script[^>]+id=["\']'
        r'__NEXT_DATA__["\'][^>]*>'
        r"(.*?)"
        r"</script\s*>"
    )

    match = re.search(
        pattern,
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return None

    raw = match.group(1).strip()

    try:
        return json.loads(raw)

    except Exception:
        return None


# =========================================================
# JSON-LD
# =========================================================

def extract_event_jsonld(html):

    if not html:
        return None

    pattern = (
        r'<script[^>]+type=["\']'
        r'application/ld\+json'
        r'["\'][^>]*>'
        r"(.*?)"
        r"</script>"
    )

    matches = re.findall(
        pattern,
        html,
        re.IGNORECASE | re.DOTALL,
    )

    for raw in matches:

        try:

            data = json.loads(
                raw.strip()
            )

            if isinstance(data, dict):

                if (
                    data.get("@type") == "SportsEvent"
                    or data.get("homeTeam")
                    or data.get("awayTeam")
                ):
                    return data

            if isinstance(data, list):

                for item in data:

                    if not isinstance(item, dict):
                        continue

                    if (
                        item.get("@type")
                        == "SportsEvent"
                        or item.get("homeTeam")
                        or item.get("awayTeam")
                    ):
                        return item

        except Exception:
            continue

    return None


# =========================================================
# content
# =========================================================

def _is_match_content(candidate):
    if not isinstance(candidate, dict):
        return False

    return any(
        key in candidate
        for key in (
            "matchFacts",
            "stats",
            "lineup",
            "header",
            "general",
        )
    )


def get_content(data):

    if not isinstance(data, dict):
        return None

    direct_content = data.get("content")

    if isinstance(direct_content, dict):
        return direct_content

    paths = [
        (
            "props",
            "pageProps",
            "content",
        ),
        (
            "props",
            "pageProps",
            "data",
            "content",
        ),
        (
            "props",
            "pageProps",
            "match",
            "content",
        ),
        (
            "props",
            "pageProps",
            "matchData",
        ),
        (
            "props",
            "pageProps",
            "data",
        ),
        (
            "pageProps",
            "content",
        ),
    ]

    for path in paths:

        value = get_nested(
            data,
            *path,
        )

        if (
            isinstance(value, dict)
            and _is_match_content(value)
        ):
            return value

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if isinstance(page_props, dict):

        for key in (
            "content",
            "data",
            "match",
            "matchData",
        ):

            value = page_props.get(key)

            if (
                isinstance(value, dict)
                and _is_match_content(value)
            ):
                return value

    return None


# =========================================================
# اطلاعات پایه
# =========================================================

def _get_team_name(team):

    if not isinstance(team, dict):
        return ""

    for key in (
        "longName",
        "name",
        "shortName",
        "title",
    ):

        value = team.get(key)

        if value:
            return clean_text(value)

    return ""


def _get_team_id(team):

    if not isinstance(team, dict):
        return None

    for key in (
        "id",
        "teamId",
        "teamID",
        "team_id",
    ):

        value = team.get(key)

        if value is not None:
            return value

    return None


def _get_stage_id(tournament):

    if not isinstance(
        tournament,
        dict,
    ):
        return None

    for key in (
        "leagueId",
        "tournamentId",
        "uniqueTournamentId",
        "competitionId",
        "competitionID",
        "tournamentID",
        "leagueID",
        "id",
    ):

        value = tournament.get(key)

        if value is not None:
            return value

    return None


def _get_competition_id(tournament):

    if not isinstance(
        tournament,
        dict,
    ):
        return None

    for key in (
        "parentLeagueId",
        "parentTournamentId",
        "parentCompetitionId",
        "parentLeagueID",
        "parentTournamentID",
        "parentCompetitionID",
    ):

        value = tournament.get(key)

        if value is not None:
            return value

    return _get_stage_id(
        tournament
    )


def _find_competition_object(
    data,
    target_name=None,
):
    """
    پیدا کردن مقاوم شیء رقابت در ساختار تو‌در‌توی FotMob.

    اگر target_name داده شود، شیئی که نامش با نام خام رقابت
    مطابقت دارد در اولویت قرار می‌گیرد.
    """

    if data is None:
        return None

    target_normalized = clean_text(
        target_name or ""
    ).lower()

    candidates = []

    competition_keys = {
        "tournament",
        "league",
        "competition",
        "uniquetournament",
        "tournamentid",
        "leagueid",
        "uniquetournamentid",
        "competitionid",
        "parentleagueid",
        "parenttournamentid",
        "parentcompetitionid",
    }

    def walk(node, parent_key=""):

        if isinstance(node, dict):

            names = []

            for key in (
                "name",
                "title",
                "shortName",
                "displayName",
                "leagueName",
                "tournamentName",
                "competitionName",
            ):

                value = node.get(key)

                if value is not None:
                    text = clean_text(value)

                    if text:
                        names.append(text)

            node_name = names[0] if names else ""
            competition_id = _get_competition_id(node)
            parent_normalized = str(
                parent_key or ""
            ).replace("_", "").lower()

            is_competition_context = (
                parent_normalized in competition_keys
                or any(
                    key in node
                    for key in competition_keys
                )
                or any(
                    key in node
                    for key in (
                        "leagueName",
                        "tournamentName",
                        "competitionName",
                    )
                )
            )

            if (
                competition_id is not None
                and node_name
                and target_normalized
                and node_name.lower()
                == target_normalized
            ):
                candidates.append(
                    (
                        100,
                        node,
                    )
                )

            elif (
                competition_id is not None
                and is_competition_context
            ):
                candidates.append(
                    (
                        80,
                        node,
                    )
                )

            elif (
                node_name
                and is_competition_context
            ):
                candidates.append(
                    (
                        40,
                        node,
                    )
                )

            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    walk(value, key)

        elif isinstance(node, list):

            for item in node:
                walk(item, parent_key)

    walk(data)

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0][1]


# =========================================================
# اطلاعات رفت/برگشت، مجموع و هفته/مرحله/راند
# =========================================================

def extract_leg_info(data):
    """
    اطلاعات رفت/برگشت را از infoBox.legInfo می‌خواند.
    مسیر تأییدشده در صفحه FotMob:
    content.matchFacts.infoBox.legInfo
    """
    info_box = get_nested(
        data,
        "props",
        "pageProps",
        "content",
        "matchFacts",
        "infoBox",
    )

    if not isinstance(info_box, dict):
        content = get_content(data)
        info_box = (
            content.get("matchFacts", {}).get("infoBox", {})
            if isinstance(content, dict)
            and isinstance(content.get("matchFacts"), dict)
            else {}
        )

    if not isinstance(info_box, dict):
        return {
            "type": None,
            "is_second_leg": False,
            "is_first_leg": False,
            "name": None,
        }

    leg_info = info_box.get("legInfo")

    if not isinstance(leg_info, dict):
        return {
            "type": None,
            "is_second_leg": False,
            "is_first_leg": False,
            "name": None,
        }

    localized = leg_info.get("localizedString")

    if not isinstance(localized, dict):
        localized = {}

    key = clean_text(localized.get("key")).lower()
    fallback = clean_text(localized.get("fallback"))

    is_second = key == "second_leg" or fallback.lower() == "2nd leg"
    is_first = key == "first_leg" or fallback.lower() == "1st leg"

    return {
        "type": "second" if is_second else "first" if is_first else None,
        "is_second_leg": is_second,
        "is_first_leg": is_first,
        "name": fallback or None,
    }


def _parse_score_text(value):
    if value is None:
        return None

    text = clean_text(value)
    match = re.search(r"(\d+)\s*[-:]\s*(\d+)", text)

    if not match:
        return None

    return {
        "home": int(match.group(1)),
        "away": int(match.group(2)),
    }


def extract_aggregate_info(data, leg_info=None):
    """
    aggregate فقط برای بازی برگشت معنی دارد.
    ابتدا مسیر رسمی infoBox.legInfo را می‌خواند و در صورت نبودن
    مقدار، کل داده را فقط برای کلیدهای مشخص aggregate جست‌وجو می‌کند.
    """
    leg_info = leg_info or extract_leg_info(data)

    empty = {
        "home": None,
        "away": None,
        "text": None,
        "winner": None,
        "loser": None,
        "tied": False,
    }

    if not leg_info.get("is_second_leg"):
        return empty

    info_box = get_nested(
        data,
        "props",
        "pageProps",
        "content",
        "matchFacts",
        "infoBox",
    )

    if not isinstance(info_box, dict):
        content = get_content(data)
        info_box = (
            content.get("matchFacts", {}).get("infoBox", {})
            if isinstance(content, dict)
            and isinstance(content.get("matchFacts"), dict)
            else {}
        )

    leg_data = (
        info_box.get("legInfo")
        if isinstance(info_box, dict)
        else None
    )

    if not isinstance(leg_data, dict):
        leg_data = {}

    aggregate = _parse_score_text(
        leg_data.get("aggregatedStr")
    )

    if aggregate is None:
        aggregate = _parse_score_text(
            leg_data.get("aggregateStr")
        )

    if aggregate is None:
        aggregate_value = recursive_find(
            data,
            {
                "aggregatedStr",
                "aggregateStr",
                "aggregate",
            },
        )

        if isinstance(aggregate_value, dict):
            aggregate = _coerce_score_pair(
                aggregate_value
            )
        else:
            aggregate = _parse_score_text(
                aggregate_value
            )

    if aggregate is None:
        return {
            **empty,
            "loser": clean_text(
                leg_data.get("whoLostOnAggregated")
            ) or None,
        }

    winner = None
    loser = clean_text(
        leg_data.get("whoLostOnAggregated")
    ) or None

    if aggregate["home"] > aggregate["away"]:
        winner = "home"
    elif aggregate["away"] > aggregate["home"]:
        winner = "away"

    return {
        "home": aggregate["home"],
        "away": aggregate["away"],
        "text": f'{aggregate["home"]} - {aggregate["away"]}',
        "winner": winner,
        "loser": loser,
        "tied": aggregate["home"] == aggregate["away"],
    }


def _translate_round_name(value):
    text = clean_text(value)

    if not text:
        return None

    normalized = text.lower().strip()

    exact = {
        "group stage": "مرحله گروهی",
        "league phase": "مرحله لیگ",
        "regular season": "فصل عادی",
        "playoffs": "پلی‌آف",
        "play-off": "پلی‌آف",
        "final": "فینال",
        "bronze": "رده بندی",
        "semi-final": "نیمه‌نهایی",
        "semifinal": "نیمه‌نهایی",
        "quarter-final": "یک‌چهارم نهایی",
        "quarter-finals": "یک‌چهارم نهایی",
        "quarterfinal": "یک‌چهارم نهایی",
        "quarterfinals": "یک‌چهارم نهایی",
        "semi-finals": "نیمه‌نهایی",
        "semifinals": "نیمه‌نهایی",
        "round of 8": "یک‌چهارم نهایی",
        "round of 16": "یک‌هشتم نهایی",
        "1/16": "یک‌شانزدهم نهایی",
        "1/8": "یک‌هشتم نهایی",
        "1/4": "یک‌چهارم نهایی",
        "1/2": "نیمه‌نهایی",
        "round of 32": "یک‌شانزدهم نهایی",
        "round of 64": "یک‌سی‌ودوم نهایی",
        "3rd round": "دور سوم",
        "4th round": "دور چهارم",
        "5th round": "دور پنجم",
        "1st round": "دور اول",
        "2nd round": "دور دوم",
    }

    if normalized in exact:
        return exact[normalized]

    match = re.fullmatch(
        r"(\d+)(?:st|nd|rd|th)?\s*round",
        normalized,
    )
    if match:
        return f'دور {match.group(1)}'

    match = re.search(
        r"(?:matchweek|match week|gameweek|week)\s*(\d+)",
        normalized,
    )
    if match:
        return f'هفته {match.group(1)}'

    if normalized.isdigit():
        return f'هفته {normalized}'

    return text


def extract_group_info(data):
    """
    استخراج گروه فقط از اطلاعات مربوط به همین مسابقه در FotMob.

    اولویت:
    1) ساختار صریح isGroup=True / groupName.
    2) leagueName مربوط به general خود مسابقه.
    3) Tournament.leagueName داخل matchFacts.infoBox خود مسابقه.

    از leagueNameهای عمومی/تاریخی مثل H2H استفاده نمی‌شود؛ بنابراین
    وجود گروه در مسابقات قبلی دو تیم باعث نمایش گروه اشتباه نمی‌شود.
    """
    empty = {"raw": None, "name": None, "name_fa": None, "source": None}
    if not isinstance(data, dict):
        return empty

    candidates = []

    def add_group(value, source):
        value = clean_text(value)
        if value:
            candidates.append((value, source))

    def walk_explicit_group(node, path="$"):
        if isinstance(node, dict):
            if node.get("isGroup") is True:
                add_group(node.get("groupName"), f"{path}.groupName")
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    walk_explicit_group(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                if isinstance(value, (dict, list)):
                    walk_explicit_group(value, f"{path}[{index}]")

    walk_explicit_group(data)
    if candidates:
        raw, source = candidates[0]
        return {
            "raw": raw,
            "name": raw,
            "name_fa": f"گروه {raw}",
            "source": source,
        }

    general = (get_nested(data, "props", "pageProps", "general") or (data.get("general") if isinstance(data, dict) else None))
    if isinstance(general, dict):
        league_name = clean_text(general.get("leagueName"))
        if league_name:
            match = re.search(r"\bGrp\.\s*([A-Za-z0-9]+)", league_name, re.IGNORECASE)
            if match:
                raw = clean_text(match.group(1))
                return {
                    "raw": raw,
                    "name": raw,
                    "name_fa": f"گروه {raw}",
                    "source": "props.pageProps.general.leagueName",
                }
            match = re.search(r"\bGroup\s+(?!Stage\b)([A-Za-z0-9]+)", league_name, re.IGNORECASE)
            if match:
                raw = clean_text(match.group(1))
                return {
                    "raw": raw,
                    "name": raw,
                    "name_fa": f"گروه {raw}",
                    "source": "props.pageProps.general.leagueName",
                }

    tournament = (get_nested(data, "props", "pageProps", "content", "matchFacts", "infoBox", "Tournament") or get_nested(data, "content", "matchFacts", "infoBox", "Tournament"))
    if isinstance(tournament, dict):
        league_name = clean_text(tournament.get("leagueName"))
        if league_name:
            match = re.search(r"\bGrp\.\s*([A-Za-z0-9]+)", league_name, re.IGNORECASE)
            if match:
                raw = clean_text(match.group(1))
                return {
                    "raw": raw,
                    "name": raw,
                    "name_fa": f"گروه {raw}",
                    "source": "props.pageProps.content.matchFacts.infoBox.Tournament.leagueName",
                }
            match = re.search(r"\bGroup\s+(?!Stage\b)([A-Za-z0-9]+)", league_name, re.IGNORECASE)
            if match:
                raw = clean_text(match.group(1))
                return {
                    "raw": raw,
                    "name": raw,
                    "name_fa": f"گروه {raw}",
                    "source": "props.pageProps.content.matchFacts.infoBox.Tournament.leagueName",
                }

    return empty


def extract_round_info(data):
    """
    استخراج نام هفته/مرحله/راند از ساختارهای FotMob.
    علاوه بر فیلدهای سطح بالا، اشیای tournament/league/competition
    و matchesInRound را هم بررسی می‌کند.
    """
    # -----------------------------------------------------
    # ساختار واقعی FotMob برای بعضی رقابت‌ها، از جمله
    # لیگ قهرمانان آسیا الیت:
    #
    # props.pageProps.general.matchRound = "1"
    # props.pageProps.general.leagueRoundName = "1"
    #
    # این دو فیلد را قبل از جست‌وجوی عمومی بررسی می‌کنیم تا
    # مقدار عمومی "Round" جای شماره هفته را نگیرد.
    # -----------------------------------------------------

    general = get_nested(
        data,
        "props",
        "pageProps",
        "general",
    )

    if isinstance(general, dict):

        for key in (
            "matchRound",
            "leagueRoundName",
        ):
            value = general.get(key)

            if value is None:
                continue

            raw = clean_text(value)

            if not raw:
                continue

            if raw.isdigit():
                return {
                    "raw": raw,
                    "name": raw,
                    "name_fa": f"هفته {raw}",
                }

            translated = _translate_round_name(raw)

            return {
                "raw": raw,
                "name": raw,
                "name_fa": translated or raw,
            }

    candidates = []

    api_general = data.get("general") if isinstance(data, dict) else None
    if isinstance(api_general, dict):
        for key in ("matchRound", "leagueRoundName", "roundName", "round", "matchweek", "matchWeek", "gameweek", "week", "tournamentStage", "stageName"):
            value = api_general.get(key)
            if value is not None:
                candidates.append((value, key))

    api_header = data.get("header") if isinstance(data, dict) else None
    if isinstance(api_header, dict):
        for key in ("roundName", "round", "matchweek", "matchWeek", "gameweek", "week", "tournamentStage", "stageName"):
            value = api_header.get(key)
            if value is not None:
                candidates.append((value, key))

    match_facts = get_nested(
        data,
        "props",
        "pageProps",
        "content",
        "matchFacts",
    )

    if not isinstance(match_facts, dict):
        content = get_content(data)
        match_facts = (
            content.get("matchFacts", {})
            if isinstance(content, dict)
            and isinstance(content.get("matchFacts"), dict)
            else {}
        )

    if isinstance(match_facts, dict):
        matches_in_round = match_facts.get("matchesInRound")
        if isinstance(matches_in_round, list):
            for item in matches_in_round:
                if not isinstance(item, dict):
                    continue

                # در بعضی رقابت‌ها FotMob مقدار عمومی "Round" را
                # در roundName می‌گذارد، در حالی که شماره هفته در
                # یکی از فیلدهای week/matchweek/gameweek یا round است.
                # بنابراین به محض دیدن roundName دیگر از بررسی
                # فیلدهای دقیق‌تر صرف‌نظر نمی‌کنیم.
                for key in (
                    "matchweek",
                    "matchWeek",
                    "gameweek",
                    "week",
                    "round",
                    "roundName",
                    "stageName",
                ):
                    value = item.get(key)
                    if value is not None:
                        candidates.append(
                            (value, key)
                        )

    content = get_content(data)
    if not isinstance(content, dict):
        content = {}

    containers = [
        data.get("general") if isinstance(data, dict) else None,
        data.get("header") if isinstance(data, dict) else None,
        get_nested(data, "props", "pageProps", "general"),
        get_nested(data, "props", "pageProps", "header"),
        content.get("general"),
        content.get("header"),
        content,
        match_facts,
    ]

    for container in containers:
        if not isinstance(container, dict):
            continue

        for key in (
            "roundName",
            "round",
            "matchweek",
            "matchWeek",
            "gameweek",
            "week",
            "tournamentStage",
            "stageName",
        ):
            value = container.get(key)
            if isinstance(value, dict):
                value = (
                    value.get("name")
                    or value.get("label")
                    or value.get("value")
                )
            if value is not None:
                candidates.append((value, key))

    # در بعضی پاسخ‌های FotMob، مرحله/هفته داخل شیء
    # tournament/league/competition قرار دارد.
    def collect_competition_rounds(node):
        if isinstance(node, dict):
            is_competition_object = any(
                key in node
                for key in (
                    "tournament",
                    "league",
                    "competition",
                    "uniqueTournament",
                    "leagueName",
                    "tournamentName",
                    "competitionName",
                )
            )

            if is_competition_object:
                for key in (
                    "roundName",
                    "round",
                    "matchweek",
                    "matchWeek",
                    "gameweek",
                    "week",
                    "tournamentStage",
                    "stageName",
                ):
                    value = node.get(key)
                    if isinstance(value, dict):
                        value = (
                            value.get("name")
                            or value.get("label")
                            or value.get("value")
                        )
                    if value is not None:
                        candidates.append((value, key))

            for value in node.values():
                if isinstance(value, (dict, list)):
                    collect_competition_rounds(value)

        elif isinstance(node, list):
            for item in node:
                collect_competition_rounds(item)

    collect_competition_rounds(data)

    # فیلدهای صریح هفته را بر "Round" عمومی مقدم می‌کنیم.
    # همچنین کلید منبع را نگه می‌داریم تا عددی مثل 1 را در
    # فیلدهای week/matchweek/gameweek به «هفته 1» تبدیل کنیم.
    prioritized_candidates = []
    for candidate in candidates:
        if isinstance(candidate, tuple) and len(candidate) == 2:
            prioritized_candidates.append(candidate)
        else:
            prioritized_candidates.append(
                (candidate, None)
            )

    prioritized_candidates.sort(
        key=lambda item: (
            0
            if str(item[1] or "").lower()
            in {
                "week",
                "matchweek",
                "matchweek",
                "gameweek",
            }
            else 1
        )
    )

    for value, source_key in prioritized_candidates:
        raw = clean_text(value)
        if not raw:
            continue

        # «Round» به‌تنهایی اطلاعات مرحله/هفته نمی‌دهد.
        if raw.lower() == "round":
            continue

        fa = _translate_round_name(raw)

        if raw.isdigit():
            source = str(
                source_key or ""
            ).lower()

            if source in {
                "week",
                "matchweek",
                "gameweek",
                "matchround",
                "leagueroundname",
                "roundname",
            }:
                fa = f"هفته {raw}"
            else:
                continue

        return {
            "raw": raw,
            "name": raw,
            "name_fa": fa or raw,
        }

    return {
        "raw": None,
        "name": None,
        "name_fa": None,
    }


def _build_competition_context(
    league_fa,
    round_info,
    leg_info,
    group_info=None,
):
    parts = []

    if league_fa:
        parts.append(league_fa)

    # گروه فقط وقتی اضافه می‌شود که FotMob برای همین مسابقه
    # group_info معتبر استخراج کرده باشد.
    group_name = (
        group_info.get("name_fa")
        or group_info.get("name")
        if isinstance(group_info, dict)
        else None
    )
    if group_name:
        parts.append(group_name)

    round_name = (
        round_info.get("name_fa")
        if isinstance(round_info, dict)
        else None
    )

    if round_name:
        parts.append(round_name)

    if isinstance(leg_info, dict):
        if leg_info.get("is_first_leg"):
            parts.append("رفت")
        elif leg_info.get("is_second_leg"):
            parts.append("برگشت")

    return " | ".join(parts) if parts else "نامشخص"


def is_final_result_ready(snapshot):
    """
    تعیین می‌کند finished فعلی FotMob واقعاً پایان نهایی بازی است یا نه.

    در بازی رفت/عادی، finished کافی است.
    در بازی برگشت، اگر aggregate مساوی باشد باید تا تعیین برنده
    در وقت اضافه/پنالتی صبر کنیم.
    """
    if not isinstance(snapshot, dict):
        return False

    if not snapshot.get("finished"):
        return False

    if not snapshot.get("is_second_leg"):
        return True

    # اگر بازی برگشت در پایان 90 دقیقه aggregate مساوی باشد،
    # باید منتظر وقت اضافه/پنالتی بمانیم.

    aggregate = snapshot.get("aggregate")
    if not isinstance(aggregate, dict):
        return True

    if not aggregate.get("tied"):
        return True

    penalty_score = snapshot.get("penalty_score")
    if isinstance(penalty_score, dict):
        return True

    # صرفاً وجود بخش پنالتی به معنی پایان نیست؛ باید برنده
    # پنالتی مشخص شده باشد. در این حالت FotMob باید
    # penalty_score را برگرداند.
    return False


def extract_basic_info(data):

    if not isinstance(data, dict):
        return {}

    general = data.get("general")

    if not isinstance(general, dict):
        general = {}

    header = data.get("header")

    if not isinstance(header, dict):
        header = {}

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if not isinstance(page_props, dict):
        page_props = {}

    page_general = page_props.get("general")

    if not isinstance(page_general, dict):
        page_general = {}

    # -----------------------------------------------------
    # content
    # -----------------------------------------------------

    content = get_content(data)

    if not isinstance(content, dict):
        content = {}

    content_general = content.get("general")

    if not isinstance(content_general, dict):
        content_general = {}

    content_header = content.get("header")

    if not isinstance(content_header, dict):
        content_header = {}

    # -----------------------------------------------------
    # تیم‌ها
    # -----------------------------------------------------

    api_teams = header.get("teams")
    if not isinstance(api_teams, dict):
        api_teams = {}

    home = (
        api_teams.get("home")
        or general.get("homeTeam")
        or page_general.get("homeTeam")
        or header.get("homeTeam")
        or content_general.get("homeTeam")
        or content_header.get("homeTeam")
        or content.get("homeTeam")
    )

    away = (
        api_teams.get("away")
        or general.get("awayTeam")
        or page_general.get("awayTeam")
        or header.get("awayTeam")
        or content_general.get("awayTeam")
        or content_header.get("awayTeam")
        or content.get("awayTeam")
    )

    if not isinstance(home, dict):
        home = {}

    if not isinstance(away, dict):
        away = {}

    home_name = _get_team_name(home)
    away_name = _get_team_name(away)

    home_id = _get_team_id(home)
    away_id = _get_team_id(away)

    # -----------------------------------------------------
    # JSON-LD
    # -----------------------------------------------------

    event_jsonld = get_nested(
        page_props,
        "seo",
        "eventJSONLD",
    )

    if not isinstance(
        event_jsonld,
        dict,
    ):
        event_jsonld = None

    if isinstance(event_jsonld, dict):

        if not home_name:

            home_name = _get_team_name(
                event_jsonld.get("homeTeam")
            )

        if not away_name:

            away_name = _get_team_name(
                event_jsonld.get("awayTeam")
            )

        if not home_id:

            home_id = _get_team_id(
                event_jsonld.get("homeTeam")
            )

        if not away_id:

            away_id = _get_team_id(
                event_jsonld.get("awayTeam")
            )

    # -----------------------------------------------------
    # fallback نام تیم
    # -----------------------------------------------------

    if not home_name:

        home_name = clean_text(
            recursive_find(
                data,
                {"homeTeamName"},
            )
            or ""
        )

    if not away_name:

        away_name = clean_text(
            recursive_find(
                data,
                {"awayTeamName"},
            )
            or ""
        )

    # -----------------------------------------------------
    # رقابت
    # -----------------------------------------------------

    # Current matchDetails API exposes direct general league fields.
    league = clean_text(general.get("leagueName") or header.get("leagueName"))
    competition_id = general.get("leagueId") or header.get("leagueId")
    stage_id = competition_id

    tournament_candidates = [
        general.get("tournament"),
        general.get("league"),
        general.get("competition"),
        general.get("uniqueTournament"),

        page_general.get("tournament"),
        page_general.get("league"),
        page_general.get("competition"),
        page_general.get("uniqueTournament"),

        header.get("tournament"),
        header.get("league"),
        header.get("competition"),
        header.get("uniqueTournament"),

        content_general.get("tournament"),
        content_general.get("league"),
        content_general.get("competition"),
        content_general.get("uniqueTournament"),

        content_header.get("tournament"),
        content_header.get("league"),
        content_header.get("competition"),
        content_header.get("uniqueTournament"),

        content.get("tournament"),
        content.get("league"),
        content.get("competition"),
        content.get("uniqueTournament"),
    ]

    tournament = None

    for candidate in tournament_candidates:

        if isinstance(candidate, dict):

            tournament = candidate
            break

        if isinstance(candidate, str) and not league:

            league = candidate

    # -----------------------------------------------------
    # استخراج اطلاعات رقابت
    # -----------------------------------------------------

    if isinstance(tournament, dict):

        league = (
            tournament.get("leagueName")
            or tournament.get("name")
            or tournament.get("title")
            or league
            or ""
        )

        stage_id = _get_stage_id(
            tournament
        )

        competition_id = _get_competition_id(
            tournament
        )

    # -----------------------------------------------------
    # اگر هنوز شناسه پیدا نشده،
    # از ساختارهای دیگر FotMob استفاده می‌کنیم.
    # -----------------------------------------------------

    if competition_id is None:

        competition_object = (
            _find_competition_object(data)
        )

        if isinstance(
            competition_object,
            dict,
        ):

            if not league:

                league = (
                    competition_object.get("leagueName")
                    or competition_object.get("name")
                    or competition_object.get("title")
                    or ""
                )

            stage_id = _get_stage_id(
                competition_object
            )

            competition_id = (
                _get_competition_id(
                    competition_object
                )
            )

    # -----------------------------------------------------
    # اگر هنوز شناسه پیدا نشده،
    # خود content را هم بررسی می‌کنیم.
    # -----------------------------------------------------

    if competition_id is None:

        competition_object = (
            _find_competition_object(content)
        )

        if isinstance(
            competition_object,
            dict,
        ):

            if not league:

                league = (
                    competition_object.get("leagueName")
                    or competition_object.get("name")
                    or competition_object.get("title")
                    or ""
                )

            stage_id = _get_stage_id(
                competition_object
            )

            competition_id = (
                _get_competition_id(
                    competition_object
                )
            )

    # -----------------------------------------------------
    # جست‌وجوی عمیق نهایی برای شناسهٔ رقابت
    # -----------------------------------------------------

    if competition_id is None:

        competition_object = (
            _find_competition_object(
                data,
                target_name=league,
            )
        )

        if isinstance(
            competition_object,
            dict,
        ):
            stage_id = _get_stage_id(
                competition_object
            )

            competition_id = (
                _get_competition_id(
                    competition_object
                )
            )

            if not league:
                league = clean_text(
                    competition_object.get("leagueName")
                    or competition_object.get("name")
                    or competition_object.get("title")
                    or competition_object.get(
                        "displayName"
                    )
                    or ""
                )

    if competition_id is None and league:

        competition_object = (
            _find_competition_object(
                content,
                target_name=league,
            )
        )

        if isinstance(
            competition_object,
            dict,
        ):
            stage_id = _get_stage_id(
                competition_object
            )

            competition_id = (
                _get_competition_id(
                    competition_object
                )
            )

    # -----------------------------------------------------
    # اگر stage_id هنوز پیدا نشده ولی competition_id
    # پیدا شده، در حالت fallback همان شناسه را نگه می‌داریم.
    # -----------------------------------------------------

    if stage_id is None:
        stage_id = competition_id

    # -----------------------------------------------------
    # fallback نام رقابت
    # -----------------------------------------------------

    if not league:

        league = clean_text(
            recursive_find(
                data,
                {
                    "leagueName",
                    "tournamentName",
                    "competitionName",
                },
            )
            or ""
        )

    # -----------------------------------------------------
    # نام فارسی رقابت
    # -----------------------------------------------------

    league_clean = clean_text(
        league
    )

    league_fa = get_persian_competition_name(
        competition_id,
        league_clean,
    )

    # -----------------------------------------------------
    # نام فارسی تیم‌ها
    # -----------------------------------------------------

    home_lookup = get_persian_team_name(
        home_id,
        home_name,
    )

    away_lookup = get_persian_team_name(
        away_id,
        away_name,
    )

    home_name_fa = (
        home_lookup
        or home_name
    )

    away_name_fa = (
        away_lookup
        or away_name
    )

    print(
        "TEAM TRANSLATION DEBUG | extract_basic_info | "
        f"translations_file={_team_translations.TEAMS_FILE} | "
        f"loaded_count={len(_team_translations._TEAM_TRANSLATIONS)} | "
        f"home_id={home_id!r} | "
        f"home_name={home_name!r} | "
        f"home_lookup={home_lookup!r} | "
        f"home_fa={home_name_fa!r} | "
        f"away_id={away_id!r} | "
        f"away_name={away_name!r} | "
        f"away_lookup={away_lookup!r} | "
        f"away_fa={away_name_fa!r}"
    )

    # -----------------------------------------------------
    # رفت/برگشت و هفته/مرحله/راند
    # -----------------------------------------------------

    leg_info = extract_leg_info(data)
    round_info = extract_round_info(data)
    group_info = extract_group_info(data)

    # -----------------------------------------------------
    # زمان
    # -----------------------------------------------------

    start = (
        general.get("matchTimeUTCDate")
        or general.get("matchTimeUTC")
        or general.get("startDate")

        or page_general.get(
            "matchTimeUTCDate"
        )
        or page_general.get(
            "matchTimeUTC"
        )
        or page_general.get(
            "startDate"
        )

        or content_general.get(
            "matchTimeUTCDate"
        )
        or content_general.get(
            "matchTimeUTC"
        )
        or content_general.get(
            "startDate"
        )
    )

    if not start and isinstance(
        event_jsonld,
        dict,
    ):

        start = event_jsonld.get(
            "startDate"
        )

    if not start:

        start = recursive_find(
            data,
            {
                "matchTimeUTCDate",
                "startDate",
                "utcTime",
            },
        )

    return {
        "home_name": clean_text(
            home_name
        ),

        "away_name": clean_text(
            away_name
        ),

        "home_name_fa": (
            home_name_fa
        ),

        "away_name_fa": (
            away_name_fa
        ),

        "home_id": home_id,

        "away_id": away_id,

        "league": league_clean,

        "league_fa": league_fa,

        "competition_id": (
            competition_id
        ),

        "stage_id": (
            stage_id
        ),

        "leg": leg_info,

        "is_second_leg": leg_info.get(
            "is_second_leg",
            False,
        ),

        "is_first_leg": leg_info.get(
            "is_first_leg",
            False,
        ),

        "aggregate": extract_aggregate_info(
            data,
            leg_info,
        ),

        "round_info": round_info,

        "group_info": group_info,

        "start": start,
    }


# =========================================================
# زمان
# =========================================================

def parse_datetime(value):

    if value is None:
        return None

    if isinstance(value, datetime):

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value

    if isinstance(value, (int, float)):

        try:

            if value > 100000000000:
                value /= 1000

            return datetime.fromtimestamp(
                value,
                tz=timezone.utc,
            )

        except Exception:
            return None

    value = str(value).strip()

    if not value:
        return None

    value = value.replace(
        "Z",
        "+00:00",
    )

    try:

        result = datetime.fromisoformat(
            value
        )

        if result.tzinfo is None:
            result = result.replace(
                tzinfo=timezone.utc
            )

        return result

    except Exception:
        pass

    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt,
            ).replace(
                tzinfo=timezone.utc
            )

        except Exception:
            continue

    return None


def format_iran_datetime(value):

    dt = parse_datetime(value)

    if dt is None:
        return "نامشخص"

    return dt.astimezone(
        IRAN_TIMEZONE
    ).strftime(
        "%Y/%m/%d - %H:%M"
    )


# =========================================================
# Match facts
# =========================================================

def _get_match_facts(data):

    content = get_content(data)

    if not isinstance(content, dict):
        return {}

    match_facts = content.get(
        "matchFacts"
    )

    if isinstance(match_facts, dict):
        return match_facts

    return {}


def _get_match_facts_events_container(data):

    match_facts = _get_match_facts(data)

    events_container = match_facts.get(
        "events"
    )

    if isinstance(events_container, dict):
        return events_container

    return {}


# =========================================================
# Event container recursive
# =========================================================

def _collect_event_lists(node, result=None):

    if result is None:
        result = []

    if isinstance(node, list):

        if node and all(
            isinstance(item, dict)
            for item in node
        ):
            result.append(node)

        for item in node:
            if isinstance(item, (dict, list)):
                _collect_event_lists(
                    item,
                    result,
                )

        return result

    if isinstance(node, dict):

        preferred_keys = (
            "events",
            "incidents",
            "chronological",
            "penaltyShootoutEvents",
            "penalty_shootout_events",
            "periods",
            "timeline",
            "items",
        )

        for key in preferred_keys:

            value = node.get(key)

            if isinstance(value, (dict, list)):
                _collect_event_lists(
                    value,
                    result,
                )

        if any(
            key in node
            for key in (
                "eventType",
                "incidentType",
                "incidentClass",
                "isGoal",
                "playerId",
                "time",
                "minute",
            )
        ):
            result.append([node])

    return result


def _get_current_match_event_candidates(data):

    candidates = []

    # -----------------------------------------------------
    # رویدادهای موجود در header
    #
    # در بعضی بازی‌های FotMob (از جمله 6054373) رویدادهای
    # کامل گل داخل این مسیر قرار دارند:
    # props.pageProps.header.events.homeTeamGoals
    # props.pageProps.header.events.awayTeamGoals
    #
    # این داده‌ها را جداگانه می‌گیریم چون ساختار آن‌ها dict
    # با کلید نام بازیکن است و _collect_event_lists برای
    # عبور از کلیدهای دلخواه طراحی نشده است.
    # -----------------------------------------------------

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if isinstance(page_props, dict):

        header = page_props.get(
            "header"
        )

        if isinstance(header, dict):

            header_events = header.get(
                "events"
            )

            if isinstance(
                header_events,
                dict,
            ):

                for key in (
                    "homeTeamGoals",
                    "awayTeamGoals",
                    "homeTeamRedCards",
                    "awayTeamRedCards",
                    "goals",
                    "cards",
                    "incidents",
                    "events",
                ):

                    value = header_events.get(
                        key
                    )

                    if isinstance(
                        value,
                        list,
                    ):

                        if value:
                            candidates.append(
                                value
                            )

                    elif isinstance(
                        value,
                        dict,
                    ):

                        for nested in value.values():

                            if isinstance(
                                nested,
                                list,
                            ):

                                if nested:
                                    candidates.append(
                                        nested
                                    )

                            elif isinstance(
                                nested,
                                dict,
                            ):

                                candidates.extend(
                                    _collect_event_lists(
                                        nested
                                    )
                                )

    # -----------------------------------------------------
    # content
    # -----------------------------------------------------

    content = get_content(data)

    if not isinstance(content, dict):
        return candidates

    match_facts = content.get(
        "matchFacts"
    )

    if isinstance(match_facts, dict):

        events_container = match_facts.get(
            "events"
        )

        if isinstance(
            events_container,
            (dict, list),
        ):

            candidates.extend(
                _collect_event_lists(
                    events_container
                )
            )

        incidents = match_facts.get(
            "incidents"
        )

        if isinstance(
            incidents,
            (dict, list),
        ):

            candidates.extend(
                _collect_event_lists(
                    incidents
                )
            )

    liveticker = content.get(
        "liveticker"
    )

    if isinstance(liveticker, dict):

        for key in (
            "events",
            "incidents",
            "timeline",
        ):

            value = liveticker.get(key)

            if isinstance(
                value,
                (dict, list),
            ):

                candidates.extend(
                    _collect_event_lists(
                        value
                    )
                )

    for key in (
        "events",
        "incidents",
        "chronological",
    ):

        value = content.get(key)

        if isinstance(
            value,
            (dict, list),
        ):

            candidates.extend(
                _collect_event_lists(
                    value
                )
            )

    return candidates


# =========================================================
# Period
# =========================================================

def _event_period_name(event):

    if not isinstance(event, dict):
        return ""

    for key in (
        "period",
        "periodName",
        "periodType",
        "matchPeriod",
        "stage",
        "stageName",
    ):

        value = event.get(key)

        if isinstance(value, dict):

            value = (
                value.get("name")
                or value.get("type")
                or value.get("key")
                or value.get("value")
            )

        if value is not None:

            text = clean_text(value)

            if text:
                return text

    return ""


def _get_match_periods(data):

    periods = []

    candidates = _get_current_match_event_candidates(
        data
    )

    for candidate in candidates:

        for event in candidate:

            period = _event_period_name(
                event
            )

            if period:
                periods.append(period)

    events_container = (
        _get_match_facts_events_container(data)
    )

    for key in (
        "period",
        "currentPeriod",
        "currentStage",
        "stage",
        "stageName",
    ):

        value = events_container.get(key)

        if isinstance(value, dict):

            value = (
                value.get("name")
                or value.get("type")
                or value.get("key")
                or value.get("value")
            )

        if value is not None:

            text = clean_text(value)

            if text:
                periods.append(text)

    unique = []

    for period in periods:

        normalized = clean_text(
            period
        ).lower()

        if normalized not in {
            clean_text(item).lower()
            for item in unique
        }:

            unique.append(period)

    return unique


def _period_flags(periods):

    normalized = {
        clean_text(period).lower()
        for period in periods
        if clean_text(period)
    }

    has_extra_time = False
    extra_time_started = False
    extra_time_finished = False
    has_penalty_shootout = False

    for period in normalized:

        compact = (
            period
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        if (
            "extrahalf" in compact
            or "halfextra" in compact
            or compact in {
                "extratime",
                "aet",
                "firstextra",
                "secondextra",
            }
        ):

            has_extra_time = True
            extra_time_started = True

            if (
                "second" in compact
                or compact in {
                    "extratime",
                    "aet",
                    "secondextra",
                    "secondextrahalf",
                }
            ):

                extra_time_finished = True

        if (
            "penaltyshootout" in compact
            or compact in {
                "shootout",
            }
        ):

            has_penalty_shootout = True

    return {
        "has_extra_time": has_extra_time,
        "extra_time_started": extra_time_started,
        "extra_time_finished": extra_time_finished,
        "has_penalty_shootout": has_penalty_shootout,
    }


# =========================================================
# Score helpers
# =========================================================

def _coerce_score_pair(value):

    if value is None:
        return None

    if isinstance(value, (list, tuple)):

        if len(value) >= 2:

            try:

                return {
                    "home": int(value[0]),
                    "away": int(value[1]),
                }

            except (
                TypeError,
                ValueError,
            ):
                return None

        return None

    if isinstance(value, dict):

        home = None
        away = None

        for key in (
            "home",
            "homeScore",
            "home_score",
            "homeTeamScore",
        ):

            if key in value:

                candidate = value.get(key)

                if isinstance(
                    candidate,
                    dict,
                ):

                    candidate = (
                        candidate.get("score")
                        or candidate.get("value")
                        or candidate.get("goals")
                    )

                if candidate is not None:

                    home = candidate
                    break

        for key in (
            "away",
            "awayScore",
            "away_score",
            "awayTeamScore",
        ):

            if key in value:

                candidate = value.get(key)

                if isinstance(
                    candidate,
                    dict,
                ):

                    candidate = (
                        candidate.get("score")
                        or candidate.get("value")
                        or candidate.get("goals")
                    )

                if candidate is not None:

                    away = candidate
                    break

        if home is not None and away is not None:

            try:

                return {
                    "home": int(home),
                    "away": int(away),
                }

            except (
                TypeError,
                ValueError,
            ):
                pass

        for key in (
            "score",
            "result",
            "value",
        ):

            nested = value.get(key)

            if nested is not None:

                result = _coerce_score_pair(
                    nested
                )

                if result is not None:
                    return result

        return None

    if isinstance(value, str):

        match = re.search(
            r"(\d+)\s*[-:]\s*(\d+)",
            value,
        )

        if match:

            return {
                "home": int(match.group(1)),
                "away": int(match.group(2)),
            }

    return None


# =========================================================
# Penalty shootout score
# =========================================================

def _contains_shootout_marker(node):

    if isinstance(node, dict):

        for key in (
            "penaltyShootout",
            "penalty_shootout",
            "shootout",
            "penaltyShootoutEvents",
            "penalty_shootout_events",
        ):

            if key in node:
                return True

        for key in (
            "period",
            "periodName",
            "periodType",
            "matchPeriod",
            "stage",
            "stageName",
        ):

            value = node.get(key)

            if isinstance(value, dict):

                value = (
                    value.get("name")
                    or value.get("type")
                    or value.get("key")
                    or value.get("value")
                )

            text = clean_text(
                value
            ).lower()

            compact = (
                text
                .replace(" ", "")
                .replace("_", "")
                .replace("-", "")
            )

            if (
                "penaltyshootout" in compact
                or compact == "shootout"
            ):
                return True

        if node.get(
            "isPenaltyShootoutEvent"
        ) is True:

            return True

        for key in (
            "incidentType",
            "eventType",
            "incidentClass",
        ):

            value = node.get(key)

            if isinstance(value, dict):

                value = (
                    value.get("name")
                    or value.get("type")
                    or value.get("key")
                    or value.get("value")
                )

            text = clean_text(
                value
            ).lower()

            compact = (
                text
                .replace(" ", "")
                .replace("_", "")
                .replace("-", "")
            )

            if (
                "penaltyshootout" in compact
                or compact == "shootout"
            ):
                return True

        for value in node.values():

            if isinstance(
                value,
                (dict, list),
            ):

                if _contains_shootout_marker(
                    value
                ):
                    return True

    elif isinstance(node, list):

        for item in node:

            if _contains_shootout_marker(
                item
            ):
                return True

    return False


def _find_penalty_score_in_shootout_section(
    section
):

    if isinstance(section, dict):

        for key in (
            "penaltyScore",
            "penalty_score",
            "shootoutScore",
            "shootout_score",
        ):

            if key in section:

                result = _coerce_score_pair(
                    section.get(key)
                )

                if result is not None:
                    return result

        for key in (
            "penaltyShootout",
            "penalty_shootout",
            "shootout",
            "penaltyShootoutEvents",
            "penalty_shootout_events",
        ):

            nested = section.get(key)

            if nested is None:
                continue

            result = _coerce_score_pair(
                nested
            )

            if result is not None:
                return result

            result = (
                _find_penalty_score_in_shootout_section(
                    nested
                )
            )

            if result is not None:
                return result

        penalties = section.get(
            "penalties"
        )

        if isinstance(
            penalties,
            dict,
        ):

            result = _coerce_score_pair(
                penalties
            )

            if result is not None:
                return result

    elif isinstance(section, list):

        for item in section:

            result = (
                _find_penalty_score_in_shootout_section(
                    item
                )
            )

            if result is not None:
                return result

    return None


def _collect_explicit_shootout_sections(
    node,
    result=None,
):

    if result is None:
        result = []

    if isinstance(node, dict):

        explicit_keys = (
            "penaltyShootout",
            "penalty_shootout",
            "shootout",
            "penaltyShootoutEvents",
            "penalty_shootout_events",
        )

        for key in explicit_keys:

            if key in node:

                value = node.get(key)

                if isinstance(
                    value,
                    (dict, list),
                ):

                    result.append(value)

                    _collect_explicit_shootout_sections(
                        value,
                        result,
                    )

        for key, value in node.items():

            if key in explicit_keys:
                continue

            if isinstance(
                value,
                (dict, list),
            ):

                _collect_explicit_shootout_sections(
                    value,
                    result,
                )

    elif isinstance(node, list):

        for item in node:

            if isinstance(
                item,
                (dict, list),
            ):

                _collect_explicit_shootout_sections(
                    item,
                    result,
                )

    return result


def _get_shootout_score_from_events(data):

    candidates = (
        _get_current_match_event_candidates(
            data
        )
    )

    home_score = 0
    away_score = 0
    found = False
    seen_shootout_events = set()

    for candidate in candidates:

        for event in candidate:

            if not isinstance(event, dict):
                continue

            # بعضی پاسخ‌های FotMob یک ضربه پنالتی را در چند مسیر
            # مختلف برمی‌گردانند. قبل از شمارش باید همان رویداد را
            # فقط یک بار حساب کنیم؛ وگرنه مثلاً 4-8 به 8-16 تبدیل می‌شود.
            # در ضربات پنالتی ممکن است یک ضربه از چند مسیر API
            # با reactKey/id متفاوت تکرار شود. هویت اصلی ضربه را
            # بر اساس زننده + تیم می‌سازیم؛ اگر زننده شناخته نباشد،
            # تیم + دقیقه/زمان + وضعیت تبدیل شدن را استفاده می‌کنیم.
            player_id = event.get("playerId")
            team_id = event.get("teamId")
            player_name = event.get("playerName")
            minute = event.get("minute")
            event_time = event.get("time")

            if player_id not in (None, "", 0, "0"):
                event_key = (
                    "player",
                    str(player_id),
                    str(team_id),
                )
            elif player_name:
                event_key = (
                    "player_name",
                    clean_text(player_name).lower(),
                    str(team_id),
                )
            else:
                event_key = (
                    "attempt",
                    str(team_id),
                    str(event.get("isHome")),
                    str(minute),
                    str(event_time),
                    str(
                        event.get("isScored")
                        if event.get("isScored") is not None
                        else event.get("scored")
                    ),
                )

            event_key = str(event_key)

            if event_key in seen_shootout_events:
                continue

            seen_shootout_events.add(event_key)

            if not _is_penalty_shootout_event(
                event
            ):
                continue

            found = True

            scored = None

            for key in (
                "isGoal",
                "isScored",
                "scored",
                "converted",
                "success",
                "successful",
            ):

                if key in event:

                    value = event.get(key)

                    if isinstance(
                        value,
                        bool,
                    ):

                        scored = value
                        break

            event_text = " ".join(
                str(event.get(key, ""))
                for key in (
                    "type",
                    "eventType",
                    "incidentType",
                    "incidentClass",
                    "description",
                    "reason",
                )
            ).lower()

            if any(
                word in event_text
                for word in (
                    "miss",
                    "saved",
                    "save",
                    "off target",
                    "woodwork",
                )
            ):

                scored = False

            if scored is False:
                continue

            if scored is None:
                scored = True

            if not scored:
                continue

            is_home = event.get(
                "isHome"
            )

            if is_home is None:

                team = event.get(
                    "team"
                )

                if isinstance(
                    team,
                    dict,
                ):

                    is_home = (
                        team.get("isHome")
                        if "isHome" in team
                        else team.get("home")
                    )

            if is_home is True:
                home_score += 1

            elif is_home is False:
                away_score += 1

    if (
        found
        and (
            home_score > 0
            or away_score > 0
        )
    ):

        return {
            "home": home_score,
            "away": away_score,
        }

    return None


def _get_penalty_score_from_page(
    data
):

    if not isinstance(data, dict):
        return None

    match_id = recursive_find(
        data,
        {
            "matchId",
            "matchID",
            "match_id",
        },
    )

    match_id = extract_match_id(
        match_id
    )

    if not match_id:
        return None

    html = fetch_match_page(
        match_id
    )

    if not html:
        return None

    patterns = [
        r"\bPen(?:alties)?\s*:\s*"
        r"(\d+)\s*[-:]\s*(\d+)",

        r"\bPenalty\s+shootout"
        r"[^0-9]{0,100}"
        r"(\d+)\s*[-:]\s*(\d+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            html,
            re.IGNORECASE | re.DOTALL,
        )

        if match:

            try:

                return {
                    "home": int(
                        match.group(1)
                    ),
                    "away": int(
                        match.group(2)
                    ),
                }

            except (
                TypeError,
                ValueError,
            ):
                continue

    return None


def get_penalty_shootout_score(data):

    if not isinstance(data, dict):
        return None

    content = get_content(data)

    if not isinstance(content, dict):
        return None

    exact_score_keys = (
        "penaltyScore",
        "penalty_score",
        "shootoutScore",
        "shootout_score",
    )

    for key in exact_score_keys:

        value = content.get(key)

        if value is not None:

            result = _coerce_score_pair(
                value
            )

            if result is not None:
                return result

    shootout_sections = (
        _collect_explicit_shootout_sections(
            content
        )
    )

    has_explicit_shootout = bool(
        shootout_sections
    )

    for section in shootout_sections:

        result = (
            _find_penalty_score_in_shootout_section(
                section
            )
        )

        if result is not None:
            return result

    if (
        has_explicit_shootout
        or _contains_shootout_marker(
            content
        )
    ):

        # API is the primary source. Do not make an HTML request
        # merely because an explicit shootout marker exists but the
        # penalty score itself is not exposed here. HTML remains the
        # full-response backup when the API payload is unusable.
        pass

    event_score = (
        _get_shootout_score_from_events(
            data
        )
    )

    if event_score is not None:
        return event_score

    match_facts = content.get(
        "matchFacts"
    )

    if isinstance(match_facts, dict):

        if _contains_shootout_marker(
            match_facts
        ):

            result = (
                _find_penalty_score_in_shootout_section(
                    match_facts
                )
            )

            if result is not None:
                return result

            # Keep the primary API path HTML-free. If the API
            # response itself is unusable, the caller uses HTML backup.

    return None


def get_match_phase_info(data):

    periods = _get_match_periods(data)

    flags = _period_flags(periods)

    penalty_score = (
        get_penalty_shootout_score(data)
    )

    if penalty_score is not None:

        flags[
            "has_penalty_shootout"
        ] = True

    current_period = (
        periods[-1]
        if periods
        else None
    )

    return {
        "periods": periods,
        "current_period": current_period,
        "has_extra_time": flags[
            "has_extra_time"
        ],
        "extra_time_started": flags[
            "extra_time_started"
        ],
        "extra_time_finished": flags[
            "extra_time_finished"
        ],
        "penalty_shootout": flags[
            "has_penalty_shootout"
        ],
        "penalty_score": penalty_score,
    }


# =========================================================
# وضعیت بازی
# =========================================================

def _find_status_objects(data):

    result = []

    if not isinstance(data, dict):
        return result

    header = data.get("header")

    if isinstance(header, dict):

        status = header.get("status")

        if isinstance(status, dict):
            result.append(status)

    general = data.get("general")

    if isinstance(general, dict):

        status = general.get("status")

        if isinstance(status, dict):
            result.append(status)

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if isinstance(page_props, dict):

        status = page_props.get("status")

        if isinstance(status, dict):
            result.append(status)

        page_header = page_props.get(
            "header"
        )

        if isinstance(page_header, dict):

            status = page_header.get(
                "status"
            )

            if isinstance(status, dict):
                result.append(status)

    content = get_content(data)

    if isinstance(content, dict):

        status = content.get("status")

        if isinstance(status, dict):
            result.append(status)

        match_facts = content.get(
            "matchFacts"
        )

        if isinstance(match_facts, dict):

            status = match_facts.get(
                "status"
            )

            if isinstance(status, dict):
                result.append(status)

            events_container = match_facts.get(
                "events"
            )

            if isinstance(
                events_container,
                dict,
            ):

                status = events_container.get(
                    "status"
                )

                if isinstance(status, dict):
                    result.append(status)

    return result


def _status_text(status):

    if not isinstance(status, dict):
        return ""

    parts = []

    reason = status.get("reason")

    if isinstance(reason, dict):

        parts.extend(
            [
                reason.get("short", ""),
                reason.get("long", ""),
                reason.get("shortKey", ""),
            ]
        )

    else:

        parts.append(reason or "")

    for key in (
        "name",
        "short",
        "long",
        "description",
        "type",
    ):

        parts.append(
            status.get(key, "")
        )

    return " ".join(
        str(part)
        for part in parts
        if part is not None
    ).lower()


def _get_match_events_ongoing(data):

    events_container = (
        _get_match_facts_events_container(data)
    )

    if not events_container:
        return None

    ongoing = events_container.get(
        "ongoing"
    )

    if isinstance(ongoing, bool):
        return ongoing

    return None


def get_match_status(data):

    statuses = _find_status_objects(data)

    started = False
    finished = False
    cancelled = False
    half_time = False
    suspended = False

    for status in statuses:

        if status.get("started") is True:
            started = True

        if status.get("finished") is True:
            finished = True

        if status.get("cancelled") is True:
            cancelled = True

        status_text = _status_text(status)

        if (
            "half time" in status_text
            or "halftime" in status_text
            or re.search(
                r"\bht\b",
                status_text,
            )
            or "first break" in status_text
            or "second break" in status_text
        ):

            half_time = True

        if any(
            text in status_text
            for text in (
                "suspended",
                "postponed",
                "interrupted",
            )
        ):

            suspended = True

    phase = get_match_phase_info(data)

    if phase["periods"] and not started:
        started = True

    if finished:
        started = True

    events_ongoing = (
        _get_match_events_ongoing(data)
    )

    if (
        not finished
        and started
        and not cancelled
        and not suspended
        and events_ongoing is False
    ):

        finished = True

    if (
        not finished
        and phase["penalty_score"] is not None
    ):

        finished = True
        started = True

    return {
        "started": started,
        "finished": finished,
        "cancelled": cancelled,
        "half_time": half_time,
        "suspended": suspended,
        "has_extra_time": phase[
            "has_extra_time"
        ],
        "extra_time_started": phase[
            "extra_time_started"
        ],
        "extra_time_finished": phase[
            "extra_time_finished"
        ],
        "penalty_shootout": phase[
            "penalty_shootout"
        ],
        "penalty_score": phase[
            "penalty_score"
        ],
        "current_period": phase[
            "current_period"
        ],
        "periods": phase[
            "periods"
        ],
    }


def get_match_status_key(data):

    status = get_match_status(data)

    if status["cancelled"]:
        return "cancelled"

    if status["finished"]:
        return "finished"

    if status["penalty_shootout"]:
        return "penalty_shootout"

    if (
        status["has_extra_time"]
        and status["extra_time_started"]
    ):
        return "extra_time"

    if status["half_time"]:
        return "half_time"

    if status["started"]:
        return "started"

    return "not_started"


def is_match_started(data):

    return bool(
        get_match_status(data).get(
            "started"
        )
    )


def is_half_time(data):

    return bool(
        get_match_status(data).get(
            "half_time"
        )
    )


# =========================================================
# Lineup
# =========================================================

def get_lineup_section(data):

    if not isinstance(data, dict):
        return None

    content = get_content(data)

    candidates = []

    if isinstance(content, dict):
        candidates.append(
            content.get("lineup")
        )

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if isinstance(page_props, dict):
        candidates.append(
            page_props.get("lineup")
        )

    candidates.append(
        data.get("lineup")
    )

    for candidate in candidates:

        if isinstance(candidate, dict):
            return candidate

    found = recursive_find(
        data,
        {"lineup"},
    )

    if isinstance(found, dict):
        return found

    return None


def get_lineup(data):
    return get_lineup_section(data)


def get_lineup_teams(data):

    lineup = get_lineup_section(data)

    if not isinstance(lineup, dict):
        return []

    for key in (
        "lineup",
        "lineups",
        "teams",
    ):

        candidate = lineup.get(key)

        if isinstance(candidate, list):
            return candidate

        if isinstance(candidate, dict):

            result = []

            for side in (
                "home",
                "away",
                "homeTeam",
                "awayTeam",
            ):

                team = candidate.get(side)

                if isinstance(team, dict):
                    result.append(team)

            if result:
                return result

    result = []

    for key in (
        "home",
        "away",
        "homeTeam",
        "awayTeam",
        "homeTeamData",
        "awayTeamData",
    ):

        team = lineup.get(key)

        if isinstance(team, dict):
            result.append(team)

    return result


def get_team_id(team):

    if not isinstance(team, dict):
        return None

    return (
        team.get("teamId")
        or team.get("id")
        or team.get("teamID")
        or team.get("team_id")
    )


def get_team_players(team):

    if not isinstance(team, dict):
        return []

    for key in (
        "players",
        "lineup",
        "starters",
    ):

        value = team.get(key)

        if isinstance(value, list):
            return value

    return []


def get_starters(team):

    if not isinstance(team, dict):
        return []

    starters = team.get("starters")

    if isinstance(starters, list):
        return starters

    players = get_team_players(team)

    result = []

    for player in players:

        if not isinstance(player, dict):
            continue

        if player.get("starter") is True:
            result.append(player)
            continue

        if player.get("isStarter") is True:
            result.append(player)
            continue

        if player.get("bench") is True:
            continue

        if player.get("isSubstitute") is True:
            continue

        if (
            player.get("timeSubbedOn") is None
            and player.get("substitute") is not True
        ):

            result.append(player)

    return result


def get_substitutes(team):

    if not isinstance(team, dict):
        return []

    for key in (
        "substitutes",
        "bench",
        "subs",
    ):

        value = team.get(key)

        if isinstance(value, list):
            return value

        if isinstance(value, dict):

            for nested_key in (
                "players",
                "benchArr",
                "substitutes",
            ):

                nested = value.get(
                    nested_key
                )

                if isinstance(nested, list):

                    flattened = []

                    for item in nested:

                        if isinstance(item, list):
                            flattened.extend(item)

                        elif isinstance(item, dict):
                            flattened.append(item)

                    if flattened:
                        return flattened

    players = get_team_players(team)

    result = []

    for player in players:

        if not isinstance(player, dict):
            continue

        if player.get("isSubstitute") is True:
            result.append(player)
            continue

        if player.get("substitute") is True:
            result.append(player)
            continue

        if player.get("bench") is True:
            result.append(player)

    return result


def get_lineup_type(data):

    lineup = get_lineup_section(data)

    if not isinstance(lineup, dict):
        return None

    for key in (
        "lineupType",
        "type",
        "lineupStatus",
    ):

        value = lineup.get(key)

        if value is None:
            continue

        value = str(value).lower()

        if "confirm" in value:
            return "confirmed"

        if "standard" in value:
            return "standard"

        return value

    return None


# =========================================================
# بازیکنان
# =========================================================

def get_player_id(player):

    if not isinstance(player, dict):
        return None

    for key in (
        "id",
        "playerId",
        "player_id",
        "playerID",
    ):

        value = player.get(key)

        if value is not None:
            return value

    nested = player.get("player")

    if isinstance(nested, dict):

        for key in (
            "id",
            "playerId",
            "player_id",
            "playerID",
        ):

            value = nested.get(key)

            if value is not None:
                return value

    return recursive_find(
        player,
        {
            "playerId",
            "player_id",
            "playerID",
        },
    )


def get_player_name(player):

    if not isinstance(player, dict):
        return ""

    name = (
        player.get("name")
        or player.get("playerName")
        or player.get("shortName")
    )

    if isinstance(name, dict):

        name = (
            name.get("full")
            or name.get("display")
            or name.get("name")
        )

    if name:
        return clean_text(name)

    nested = player.get("player")

    if isinstance(nested, dict):

        name = (
            nested.get("name")
            or nested.get("shortName")
            or nested.get("playerName")
        )

        if name:
            return clean_text(name)

    return ""


def _rating_from_value(value):

    if value is None:
        return None

    if isinstance(value, dict):

        for key in (
            "num",
            "value",
            "rating",
            "score",
        ):

            nested = value.get(key)

            if nested is not None:

                result = _rating_from_value(
                    nested
                )

                if result is not None:
                    return result

        return None

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return None

        value = value.replace(",", ".")

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):

        return None

    if number < 0 or number > 10:
        return None

    return number


def get_player_rating(player):

    if not isinstance(player, dict):
        return None

    for key in (
        "rating",
        "ratingNum",
        "matchRating",
        "performanceRating",
    ):

        if key in player:

            rating = _rating_from_value(
                player.get(key)
            )

            if rating is not None:
                return rating

    for key in (
        "stats",
        "performance",
        "matchStats",
        "playerStats",
        "ratingData",
    ):

        value = player.get(key)

        if isinstance(value, dict):

            for rating_key in (
                "rating",
                "ratingNum",
                "matchRating",
                "performanceRating",
            ):

                rating = _rating_from_value(
                    value.get(rating_key)
                )

                if rating is not None:
                    return rating

    nested_player = player.get("player")

    if isinstance(nested_player, dict):

        rating = get_player_rating(
            nested_player
        )

        if rating is not None:
            return rating

    return None


# =========================================================
# مربی / آرایش
# =========================================================

def get_coach(team):

    if not isinstance(team, dict):
        return ""

    for key in (
        "coach",
        "manager",
        "headCoach",
    ):

        value = team.get(key)

        if isinstance(value, str):
            return clean_text(value)

        if isinstance(value, dict):

            name = (
                value.get("name")
                or value.get("fullName")
                or value.get("shortName")
            )

            if name:
                return clean_text(name)

    return ""


def get_formation(team):

    if not isinstance(team, dict):
        return ""

    for key in (
        "formation",
        "formationString",
        "displayFormation",
    ):

        value = team.get(key)

        if isinstance(value, str):
            return clean_text(value)

    return ""


def get_player_position(player):

    if not isinstance(player, dict):
        return ""

    position = (
        player.get("position")
        or player.get("role")
        or player.get("positionStringShort")
    )

    if isinstance(position, dict):

        position = (
            position.get("name")
            or position.get("short")
            or position.get("value")
        )

    return str(position or "").lower()


def organize_players(players, formation=None):

    groups = {
        "goalkeeper": [],
        "defender": [],
        "midfielder": [],
        "attacker": [],
        "unknown": [],
    }

    if not isinstance(players, list):
        return groups

    for player in players:

        position = get_player_position(
            player
        )

        if (
            "goal" in position
            or position in {
                "gk",
                "keeper",
                "goalkeeper",
            }
        ):

            groups["goalkeeper"].append(player)

        elif any(
            word in position
            for word in (
                "def",
                "back",
                "centre-back",
                "center-back",
                "cb",
                "lb",
                "rb",
                "lwb",
                "rwb",
            )
        ):

            groups["defender"].append(player)

        elif any(
            word in position
            for word in (
                "mid",
                "dm",
                "cm",
                "am",
                "lm",
                "rm",
            )
        ):

            groups["midfielder"].append(player)

        elif any(
            word in position
            for word in (
                "attack",
                "forward",
                "striker",
                "st",
                "cf",
                "lw",
                "rw",
                "wing",
            )
        ):

            groups["attacker"].append(player)

        else:

            groups["unknown"].append(player)

    return groups


# =========================================================
# Event helpers
# =========================================================

def get_event_player_id(event):

    if not isinstance(event, dict):
        return None

    for key in (
        "playerId",
        "player_id",
        "playerID",
    ):

        value = event.get(key)

        if value is not None:
            return value

    player = event.get("player")

    if isinstance(player, dict):

        for key in (
            "id",
            "playerId",
            "player_id",
            "playerID",
        ):

            value = player.get(key)

            if value is not None:
                return value

    return recursive_find(
        event,
        {
            "playerId",
            "player_id",
            "playerID",
        },
    )


def get_event_assist_player_id(event):

    if not isinstance(event, dict):
        return None

    for key in (
        "assistPlayerId",
        "assist_player_id",
        "assistantPlayerId",
        "assistant_player_id",
    ):

        value = event.get(key)

        if value is not None:
            return value

    for key in (
        "assist",
        "assistant",
    ):

        value = event.get(key)

        if isinstance(value, dict):

            for id_key in (
                "id",
                "playerId",
                "player_id",
            ):

                player_id = value.get(
                    id_key
                )

                if player_id is not None:
                    return player_id

    return None


def get_event_unique_id(event):

    if not isinstance(event, dict):
        return None

    for key in (
        "id",
        "eventId",
        "eventID",
        "incidentId",
        "incidentID",
    ):

        value = event.get(key)

        if value is not None:
            return value

    return None


def _is_penalty_shootout_event(event):

    if not isinstance(event, dict):
        return False

    if event.get(
        "isPenaltyShootoutEvent"
    ) is True:

        return True

    for key in (
        "period",
        "periodName",
        "periodType",
        "matchPeriod",
        "stage",
        "stageName",
    ):

        value = event.get(key)

        if isinstance(value, dict):

            value = (
                value.get("name")
                or value.get("type")
                or value.get("key")
                or value.get("value")
            )

        text = clean_text(value).lower()

        compact = (
            text
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        if (
            "penaltyshootout" in compact
            or compact == "shootout"
        ):

            return True

    for key in (
        "incidentType",
        "eventType",
        "incidentClass",
    ):

        value = event.get(
            key,
            "",
        )

        if isinstance(value, dict):

            value = (
                value.get("name")
                or value.get("type")
                or value.get("key")
                or value.get("value")
            )

        text = clean_text(
            value
        ).lower()

        compact = (
            text
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        if (
            "penaltyshootout" in compact
            or compact == "shootout"
        ):

            return True

    return False


def normalize_event(event):

    if not isinstance(event, dict):
        return None

    result = dict(event)

    is_shootout = (
        _is_penalty_shootout_event(event)
    )

    if is_shootout:

        result[
            "isPenaltyShootoutEvent"
        ] = True

        result["type"] = (
            "penalty_shootout"
        )

    else:

        event_type = (
            event.get("type")
            or event.get("eventType")
            or event.get("incidentType")
            or event.get("incident")
            or ""
        )

        if isinstance(
            event_type,
            dict,
        ):

            event_type = (
                event_type.get("name")
                or event_type.get("type")
                or ""
            )

        event_type = str(
            event_type
        ).lower()

        if (
            "goal" in event_type
            or event.get("isGoal") is True
        ):

            result["type"] = "goal"

        elif (
            "card" in event_type
            or event.get("card") is not None
            or event.get("cardType") is not None
        ):

            result["type"] = "card"

        elif "var" in event_type:

            result["type"] = "var"

        else:

            result["type"] = event_type

    player_id = get_event_player_id(
        event
    )

    if player_id is not None:
        result["playerId"] = player_id

    assist_id = get_event_assist_player_id(
        event
    )

    if assist_id is not None:
        result["assistPlayerId"] = assist_id

    if "isHome" in event:

        result["isHome"] = event["isHome"]

    elif "home" in event:

        result["isHome"] = event["home"]

    elif "team" in event:

        team = event["team"]

        if isinstance(team, dict):

            if "isHome" in team:
                result["isHome"] = team["isHome"]

            elif "home" in team:
                result["isHome"] = team["home"]

    return result


# =========================================================
# استخراج Eventها
# =========================================================

def _normalize_event_list(candidate):

    if not isinstance(candidate, list):
        return []

    result = []

    for event in candidate:

        normalized = normalize_event(
            event
        )

        if normalized is not None:
            result.append(normalized)

    return result


def _dedupe_events(events):

    result = []
    seen = set()

    for event in events:

        if not isinstance(
            event,
            dict,
        ):
            continue

        # reactKey در داده‌های فعلی FotMob شناسه یکتای واقعی
        # event است. eventId در بعضی بازی‌ها برای چند event
        # مختلف مقدار 0 دارد، بنابراین نباید اولویت داشته باشد.
        react_key = event.get(
            "reactKey"
        )

        if react_key is not None and str(
            react_key
        ).strip():

            key = (
                "react",
                str(react_key),
            )

        else:

            event_id = get_event_unique_id(
                event
            )

            # eventId=0 در بعضی صفحات FotMob مقدار placeholder
            # است و برای dedupe قابل اعتماد نیست.
            if (
                event_id is not None
                and str(event_id) != "0"
            ):

                key = (
                    "id",
                    str(event_id),
                )

            else:

                key = (
                    "fallback",
                    str(event.get("type", "")),
                    str(event.get("playerId", "")),
                    str(event.get("time", "")),
                    str(event.get("minute", "")),
                    str(event.get("isHome", "")),
                    str(event.get("ownGoal", "")),
                    str(event.get("isPenaltyShootoutEvent", "")),
                )

        if key in seen:
            continue

        seen.add(key)
        result.append(event)

    return result


def extract_events_from_data(data):

    if not isinstance(data, dict):
        return []

    candidates = (
        _get_current_match_event_candidates(
            data
        )
    )

    all_events = []

    for candidate in candidates:

        normalized = _normalize_event_list(
            candidate
        )

        if normalized:
            all_events.extend(normalized)

    if all_events:

        return _dedupe_events(
            all_events
        )

    return []


def get_match_events(match_url):

    match_id = extract_match_id(
        match_url
    )

    if not match_id:
        return []

    data = fetch_match_api(
        match_id
    )

    if isinstance(data, dict):

        events = extract_events_from_data(
            data
        )

        if events:
            print(f"FotMob {match_id}: events from API PRIMARY ({len(events)}).")
            return events

        status = get_match_status(data)
        if not status.get("started"):
            print(f"FotMob {match_id}: API reports no pre-match events.")
            return []
        print(f"FotMob {match_id}: API events empty; trying HTML BACKUP.")

    page = fetch_match_page(
        match_id
    )

    if not page:
        return []

    next_data = extract_next_data(
        page
    )

    if isinstance(next_data, dict):

        return extract_events_from_data(
            next_data
        )

    return []


# =========================================================
# Score
# =========================================================

def get_score(data):

    if not isinstance(data, dict):

        return {
            "home": 0,
            "away": 0,
        }

    header = data.get("header")

    status = {}

    if isinstance(header, dict):

        status = header.get("status")

        if not isinstance(status, dict):
            status = {}

    candidates = [
        status.get("score"),
        data.get("score"),
        get_nested(
            data,
            "props",
            "pageProps",
            "header",
            "status",
            "score",
        ),
    ]

    for score in candidates:

        if not isinstance(score, dict):
            continue

        home = (
            score.get("home")
            if score.get("home") is not None
            else score.get("homeScore")
        )

        away = (
            score.get("away")
            if score.get("away") is not None
            else score.get("awayScore")
        )

        try:

            if (
                home is not None
                and away is not None
            ):

                return {
                    "home": int(home),
                    "away": int(away),
                }

        except (
            TypeError,
            ValueError,
        ):
            pass

    score_strings = [
        status.get("scoreStr"),
        data.get("scoreStr"),
        get_nested(
            data,
            "props",
            "pageProps",
            "header",
            "status",
            "scoreStr",
        ),
    ]

    for score_str in score_strings:

        if score_str is None:
            continue

        match = re.search(
            r"(\d+)\s*[-:]\s*(\d+)",
            str(score_str),
        )

        if match:

            return {
                "home": int(match.group(1)),
                "away": int(match.group(2)),
            }

    return {
        "home": 0,
        "away": 0,
    }


# =========================================================
# آمار بازی
# =========================================================

STAT_ALIASES = {
    "expected goals": "xG",
    "expected goals (xg)": "xG",
    "xg": "xG",

    "xg on target": "xGOT",
    "xg on target (xgot)": "xGOT",
    "expected goals on target": "xGOT",

    "shots": "شوت",
    "total shots": "شوت",

    "shots on target": "شوت در چارچوب",

    "shots off target": "شوت خارج از چارچوب",

    "blocked shots": "شوت بلوکه‌شده",

    "hit woodwork": "تیرک",

    "shots inside box": "شوت داخل محوطه",

    "shots outside box": "شوت خارج محوطه",

    "possession": "مالکیت",
    "ball possession": "مالکیت",

    "passes": "پاس",
    "total passes": "پاس",

    "accurate passes": "پاس دقیق",
    "accurate passes (%)": "پاس دقیق",

    "pass accuracy": "دقت پاس",

    "own half": "پاس در نیمه خودی",
    "own half passes": "پاس در نیمه خودی",

    "opposition half": "پاس در نیمه حریف",
    "opposition half passes": "پاس در نیمه حریف",

    "accurate long balls": "پاس بلند دقیق",
    "accurate crosses": "سانتر دقیق",

    "throws": "پرتاب",

    "touches in opposition box": (
        "لمس توپ در محوطه حریف"
    ),

    "big chances": "موقعیت بزرگ",
    "big chances missed": "موقعیت بزرگ از دست‌رفته",

    "corners": "کرنر",
    "corner kicks": "کرنر",

    "tackles": "تکل",
    "interceptions": "قطع توپ",
    "blocks": "بلاک",
    "clearances": "دفع توپ",
    "keeper saves": "مهار دروازه‌بان",

    "duels won": "دوئل‌های برده‌شده",
    "ground duels won": "دوئل زمینی برده‌شده",
    "aerial duels won": "دوئل هوایی برده‌شده",
    "successful dribbles": "دریبل موفق",

    "fouls": "خطا",
    "fouls committed": "خطا",

    "offsides": "آفساید",

    "yellow cards": "کارت زرد",
    "red cards": "کارت قرمز",
}


def _normalize_stat_label(value):

    value = clean_text(value).lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return STAT_ALIASES.get(
        value
    )


def _stat_value(value):

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):

        text = clean_text(value)

        if not text:
            return None

        if "(" in text or "%" in text:
            return text

        try:
            number = float(text)

            if number.is_integer():
                return int(number)

            return number

        except (
            TypeError,
            ValueError,
        ):

            return text

    return None


def _team_name_matches(
    value,
    home_name,
    away_name,
):

    if value is None:
        return None

    if isinstance(value, dict):

        value = (
            value.get("name")
            or value.get("shortName")
            or value.get("longName")
            or value.get("title")
        )

    text = clean_text(
        value
    ).lower()

    if not text:
        return None

    home = clean_text(
        home_name
    ).lower()

    away = clean_text(
        away_name
    ).lower()

    if (
        text == home
        or text in home
        or home in text
    ):

        return "home"

    if (
        text == away
        or text in away
        or away in text
    ):

        return "away"

    return None


def _extract_stat_pair(
    item,
    home_name,
    away_name,
):

    if not isinstance(item, dict):
        return None

    label = (
        item.get("title")
        or item.get("name")
        or item.get("label")
        or item.get("stat")
    )

    normalized_label = _normalize_stat_label(
        label
    )

    if normalized_label is None:
        return None

    values = item.get("stats")

    if not isinstance(values, (list, dict)):
        values = item.get("values")

    if not isinstance(values, (list, dict)):
        values = item.get("value")

    if isinstance(values, list):

        if (
            len(values) == 2
            and not all(
                isinstance(value, dict)
                for value in values
            )
        ):

            home_value = _stat_value(
                values[0]
            )

            away_value = _stat_value(
                values[1]
            )

            if (
                home_value is not None
                or away_value is not None
            ):

                return (
                    normalized_label,
                    home_value,
                    away_value,
                )

        home_value = None
        away_value = None

        for value_item in values:

            if not isinstance(
                value_item,
                dict,
            ):
                continue

            team_side = _team_name_matches(
                value_item.get("name")
                or value_item.get("team")
                or value_item.get("teamName"),
                home_name,
                away_name,
            )

            value = (
                value_item.get("value")
            )

            if value is None:
                value = value_item.get("stat")

            if value is None:
                value = value_item.get(
                    "displayValue"
                )

            value = _stat_value(value)

            if team_side == "home":
                home_value = value

            elif team_side == "away":
                away_value = value

        if (
            home_value is not None
            or away_value is not None
        ):

            return (
                normalized_label,
                home_value,
                away_value,
            )

    if isinstance(values, dict):

        home_value = None
        away_value = None

        for key, value in values.items():

            side = _team_name_matches(
                key,
                home_name,
                away_name,
            )

            value = _stat_value(value)

            if side == "home":
                home_value = value

            elif side == "away":
                away_value = value

        if (
            home_value is not None
            or away_value is not None
        ):

            return (
                normalized_label,
                home_value,
                away_value,
            )

    return None


def _walk_final_stats(
    node,
    home_name,
    away_name,
    found,
):

    if isinstance(node, dict):

        values = node.get("stats")

        is_leaf = (
            isinstance(values, list)
            and len(values) == 2
            and not all(
                isinstance(value, dict)
                for value in values
            )
        )

        if (
            is_leaf
            and node.get("type") != "title"
        ):

            result = _extract_stat_pair(
                node,
                home_name,
                away_name,
            )

            if result is not None:

                label_key = result[0]

                if label_key not in found:

                    found[label_key] = {
                        "home": result[1],
                        "away": result[2],
                    }

        for value in node.values():

            _walk_final_stats(
                value,
                home_name,
                away_name,
                found,
            )

    elif isinstance(node, list):

        for item in node:

            _walk_final_stats(
                item,
                home_name,
                away_name,
                found,
            )


def _find_periods_all(stats):

    if not isinstance(stats, dict):
        return None

    periods = stats.get("Periods")

    if not isinstance(periods, dict):
        return None

    all_period = periods.get("All")

    if isinstance(all_period, dict):
        return all_period

    return None


def extract_match_stats(
    data,
    home_name,
    away_name,
):

    if not isinstance(data, dict):
        return {}

    content = get_content(data)

    if not isinstance(content, dict):
        return {}

    stats = content.get("stats")

    if not isinstance(stats, dict):

        stats = content.get(
            "statistics"
        )

    if not isinstance(stats, dict):
        return {}

    periods_all = _find_periods_all(
        stats
    )

    if not isinstance(periods_all, dict):
        return {}

    found = {}

    _walk_final_stats(
        periods_all,
        home_name,
        away_name,
        found,
    )

    return found


# =========================================================
# Team object
# =========================================================

def build_team_object(
    team_data,
    lineup_team,
):

    if not isinstance(team_data, dict):
        team_data = {}

    if not isinstance(lineup_team, dict):
        lineup_team = {}

    result = dict(lineup_team)

    if not result.get("id"):

        result["id"] = (
            team_data.get("id")
            or team_data.get("teamId")
        )

    if not result.get("name"):

        result["name"] = (
            team_data.get("name")
            or ""
        )

    starters = get_starters(result)
    substitutes = get_substitutes(result)

    result["starters"] = starters
    result["substitutes"] = substitutes

    if not result.get("formation"):

        formation = get_formation(
            lineup_team
        )

        if formation:
            result["formation"] = formation

    if not result.get("coach"):

        coach = get_coach(
            lineup_team
        )

        if coach:
            result["coach"] = coach

    return result


# =========================================================
# Round / competition API backup
# =========================================================

def fetch_league_round_api(match_id, league_id):
    """Get the match round from FotMob's league API without HTML."""
    if not match_id or league_id is None:
        return None

    try:
        response = requests.get(
            f"{FOTMOB_BASE_URL}/api/data/leagueDataForMatch",
            params={"matchId": match_id, "leagueId": league_id},
            headers=FOTMOB_HEADERS,
            timeout=15,
        )

        print(
            f"FotMob {match_id}: "
            f"leagueDataForMatch API HTTP {response.status_code}"
        )

        if response.status_code != 200:
            return None

        payload = response.json()
        if not isinstance(payload, dict):
            return None

        current_round = (
            payload.get("currentRound")
            or payload.get("roundName")
            or payload.get("round")
        )

        return clean_text(current_round) or None

    except Exception as error:
        print(
            f"FotMob {match_id}: "
            f"leagueDataForMatch API error: {error}"
        )
        return None


# =========================================================
# Snapshot
# =========================================================

def get_match_snapshot(match_url):

    match_id = extract_match_id(
        match_url
    )

    if not match_id:

        print(
            "FotMob: Match ID not found."
        )

        return None

    data = fetch_match_api(
        match_id
    )

    if not isinstance(data, dict):

        print(f"FotMob {match_id}: switching to HTML BACKUP.")
        page = fetch_match_page(
            match_id
        )

        if not page:
            return None

        data = extract_next_data(
            page
        )

        if not isinstance(data, dict):

            print(
                f"FotMob {match_id}: "
                "Could not extract NEXT_DATA."
            )

            return None

    info = extract_basic_info(data)

    # If matchDetails has no week, use FotMob's league API.
    # This remains an API-only fallback; HTML is not involved.
    round_info = info.get("round_info")
    if not isinstance(round_info, dict) or not round_info.get("name_fa"):
        api_round = fetch_league_round_api(
            match_id,
            info.get("competition_id"),
        )
        if api_round:
            translated = _translate_round_name(api_round)
            if api_round.isdigit():
                translated = f"هفته {api_round}"
            info["round_info"] = {
                "raw": api_round,
                "name": api_round,
                "name_fa": translated or api_round,
            }

    status = get_match_status(data)

    phase = get_match_phase_info(data)

    lineup_teams = get_lineup_teams(data)

    home_id = info.get("home_id")
    away_id = info.get("away_id")

    home_lineup = None
    away_lineup = None

    for team in lineup_teams:

        team_id = get_team_id(team)

        if (
            home_id is not None
            and team_id is not None
            and str(team_id) == str(home_id)
        ):

            home_lineup = team

        elif (
            away_id is not None
            and team_id is not None
            and str(team_id) == str(away_id)
        ):

            away_lineup = team

    if home_lineup is None:

        for team in lineup_teams:

            if not isinstance(team, dict):
                continue

            name = _get_team_name(team)

            if (
                name
                and name.lower()
                == info.get(
                    "home_name",
                    "",
                ).lower()
            ):

                home_lineup = team
                break

    if away_lineup is None:

        for team in lineup_teams:

            if not isinstance(team, dict):
                continue

            name = _get_team_name(team)

            if (
                name
                and name.lower()
                == info.get(
                    "away_name",
                    "",
                ).lower()
            ):

                away_lineup = team
                break

    if (
        home_lineup is None
        and len(lineup_teams) >= 1
    ):

        home_lineup = lineup_teams[0]

    if (
        away_lineup is None
        and len(lineup_teams) >= 2
    ):

        away_lineup = lineup_teams[1]

    home_team_data = {
        "id": home_id,
        "name": info.get(
            "home_name"
        ),
    }

    away_team_data = {
        "id": away_id,
        "name": info.get(
            "away_name"
        ),
    }

    home_team = build_team_object(
        home_team_data,
        home_lineup or {},
    )

    away_team = build_team_object(
        away_team_data,
        away_lineup or {},
    )

    home_starters = get_starters(
        home_team
    )

    away_starters = get_starters(
        away_team
    )

    lineup_type = get_lineup_type(data)

    if (
        lineup_type is None
        and len(home_starters) == 11
        and len(away_starters) == 11
    ):

        lineup_type = "standard"

    home_name = (
        info.get("home_name")
        or _get_team_name(home_lineup)
        or "Home"
    )

    away_name = (
        info.get("away_name")
        or _get_team_name(away_lineup)
        or "Away"
    )

    # -----------------------------------------------------
    # اگر ID از اطلاعات پایه پیدا نشده بود،
    # از lineup می‌گیریم.
    # -----------------------------------------------------

    if home_id is None:
        home_id = get_team_id(home_lineup)

    if away_id is None:
        away_id = get_team_id(away_lineup)

    # -----------------------------------------------------
    # نام فارسی تیم‌ها
    #
    # این قسمت عمداً بعد از نهایی‌شدن IDهاست تا اگر
    # ID فقط در lineup موجود بود، ترجمه باز هم انجام شود.
    # -----------------------------------------------------

    home_lookup = get_persian_team_name(
        home_id,
        home_name,
    )

    away_lookup = get_persian_team_name(
        away_id,
        away_name,
    )

    home_name_fa = (
        home_lookup
        or home_name
    )

    away_name_fa = (
        away_lookup
        or away_name
    )

    print(
        "TEAM TRANSLATION DEBUG | get_match_snapshot | "
        f"match_id={match_id!r} | "
        f"home_id={home_id!r} | "
        f"home_name={home_name!r} | "
        f"home_lookup={home_lookup!r} | "
        f"home_fa={home_name_fa!r} | "
        f"away_id={away_id!r} | "
        f"away_name={away_name!r} | "
        f"away_lookup={away_lookup!r} | "
        f"away_fa={away_name_fa!r}"
    )

    # -----------------------------------------------------
    # نتیجه
    # -----------------------------------------------------

    score = get_score(data)

    penalty_score = phase[
        "penalty_score"
    ]

    stats = extract_match_stats(
        data,
        home_name,
        away_name,
    )

    # -----------------------------------------------------
    # نام فارسی رقابت
    #
    # دوباره بر اساس competition_id نهایی می‌شود تا
    # اگر در مرحله اول اطلاعات ناقص بود، fallback درست باشد.
    # -----------------------------------------------------

    league = (
        info.get("league")
        or "نامشخص"
    )

    league_fa = (
        get_persian_competition_name(
            info.get("competition_id"),
            league,
        )
        or info.get("league_fa")
        or league
    )

    leg_info = extract_leg_info(data)
    round_info = extract_round_info(data)
    group_info = extract_group_info(data)
    aggregate = extract_aggregate_info(
        data,
        leg_info,
    )

    print(
        f"FotMob {match_id}: competition debug | "
        f"league={league_fa!r} | "
        f"group_info={group_info!r} | "
        f"round_info={round_info!r} | "
        f"leg_info={leg_info!r} | "
        f"aggregate={aggregate!r}"
    )

    return {
        "match_id": match_id,

        # نام خام برای منطق داخلی
        "home": home_name,
        "away": away_name,

        # نام فارسی برای نمایش
        "home_fa": home_name_fa,
        "away_fa": away_name_fa,

        "home_team": home_team,

        "away_team": away_team,

        "home_team_id": home_id,

        "away_team_id": away_id,

        # نام خام رقابت
        "league": league,

        # نام فارسی رقابت
        "league_fa": league_fa,

        # شناسه رقابت اصلی
        "competition_id": (
            info.get("competition_id")
        ),

        # شناسه مرحله / نسخه رقابت
        "stage_id": (
            info.get("stage_id")
        ),

        "leg": leg_info,

        "is_second_leg": leg_info.get(
            "is_second_leg",
            False,
        ),

        "is_first_leg": leg_info.get(
            "is_first_leg",
            False,
        ),

        "aggregate": aggregate,

        "round_info": round_info,

        "group_info": group_info,

        "competition_context": _build_competition_context(
            league_fa,
            round_info,
            leg_info,
            group_info,
        ),

        "start": info.get("start"),

        "start_formatted": (
            format_iran_datetime(
                info.get("start")
            )
        ),

        "lineup_type": lineup_type,

        "home_starters": home_starters,

        "away_starters": away_starters,

        "started": status["started"],

        "half_time": status["half_time"],

        "finished": status["finished"],

        "cancelled": status["cancelled"],

        # نتیجه عادی بازی
        "score": score,

        # نتیجه ضربات پنالتی
        "penalty_score": penalty_score,

        "has_extra_time": status[
            "has_extra_time"
        ],

        "extra_time_started": status[
            "extra_time_started"
        ],

        "extra_time_finished": status[
            "extra_time_finished"
        ],

        "penalty_shootout": status[
            "penalty_shootout"
        ],

        "current_period": status[
            "current_period"
        ],

        "periods": status[
            "periods"
        ],

        "stats": stats,

        "status_key": (
            get_match_status_key(data)
        ),

        "raw": data,
    }


# =========================================================
# تابع سازگاری
# =========================================================

def get_match(match_url):

    return get_match_snapshot(
        match_url
    )
