TEAM_ID_TRANSLATIONS = {
    "8560": "رئال سوسیداد",
    "8371": "اوساسونا",
}


TEAM_NAME_TRANSLATIONS = {
    "Real Sociedad": "رئال سوسیداد",
    "Osasuna": "اوساسونا",
}


def get_persian_team_name(team_id, team_name):
    if team_id is not None:
        translated = TEAM_ID_TRANSLATIONS.get(
            str(team_id)
        )

        if translated:
            return translated

    if team_name:
        translated = TEAM_NAME_TRANSLATIONS.get(
            team_name
        )

        if translated:
            return translated

    return team_name or ""
