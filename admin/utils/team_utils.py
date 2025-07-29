import os
import json

TEAMS_FILE = "data/teams.json"

DEFAULT_TEAMS = [
    "AGCC", "DAIICHI", "KMTI PJ", "KUSAKABE",
    "MINATOGUMI", "WINDSMILE",
]


def ensure_teams_file():
    """Ensure teams.json exists and return list of teams."""
    os.makedirs(os.path.dirname(TEAMS_FILE), exist_ok=True)
    if not os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, "w") as f:
            json.dump(DEFAULT_TEAMS, f, indent=4)

    try:
        with open(TEAMS_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                with open(TEAMS_FILE, "w") as wf:
                    json.dump(DEFAULT_TEAMS, wf, indent=4)
                return DEFAULT_TEAMS
            return json.loads(content)
    except json.JSONDecodeError:
        with open(TEAMS_FILE, "w") as f:
            json.dump(DEFAULT_TEAMS, f, indent=4)
        return DEFAULT_TEAMS


def save_teams(teams):
    with open(TEAMS_FILE, "w") as f:
        json.dump(teams, f, indent=4)


def get_team_options():
    """Return the latest list of team options."""
    return ensure_teams_file()
