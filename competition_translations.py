import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
COMPETITIONS_FILE = (
    BASE_DIR / "competitions.json"
)


def _load_competitions():
    try:
        with open(
            COMPETITIONS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(data, list):
        return {}

    result = {}

    for competition in data:

        if not isinstance(
            competition,
            dict,
        ):
            continue

        competition_id = competition.get(
            "id"
        )

        persian = competition.get(
            "persian"
        )

        if competition_id is None:
            continue

        if not persian:
            continue

        result[
            str(competition_id)
        ] = str(persian)

    return result


_COMPETITION_TRANSLATIONS = (
    _load_competitions()
)


# نام‌های شناخته‌شده‌ای که FotMob گاهی به‌صورت
# نام مرحله/نسخه رقابت برمی‌گرداند و ممکن است
# شناسه‌شان در competitions.json ثبت نشده باشد.
_FALLBACK_TRANSLATIONS = {
    "champions league qualification": (
        "انتخابی لیگ قهرمانان اروپا"
    ),
}


def get_persian_competition_name(
    competition_id,
    fallback_name="",
):
    if competition_id is not None:

        translated = (
            _COMPETITION_TRANSLATIONS.get(
                str(competition_id)
            )
        )

        if translated:
            return translated

    normalized_name = (
        str(fallback_name or "")
        .strip()
        .lower()
    )

    translated = _FALLBACK_TRANSLATIONS.get(
        normalized_name
    )

    if translated:
        return translated

    return fallback_name or ""
