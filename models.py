"""
Business logic functions — pure, testable, no Flask/DB imports.
"""

POSITIONS = {
    "FB":        "FB (Walker)",
    "CB":        "CB",
    "FB_DELPH":  "FB (Delph)",
    "6ER":       "6er",
    "FB_CANCELO": "FB (Cancelo)",
    "8ER":       "8er",
    "WIDE":      "Wide player",
    "CF":        "CF",
}
VALID_POSITIONS = set(POSITIONS.keys())
DISPLAY_TO_KEY = {v.upper(): k for k, v in POSITIONS.items()}

FOOT_OPTIONS   = ["Right", "Left", "Both"]
GENDER_OPTIONS = ["Male", "Female"]
CARD_OPTIONS   = ["None", "Yellow", "Red"]
RATING_OPTIONS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
RATING_DESCRIPTIONS = {
    1: "Very good performer & very suitable for our system.",
    2: "Promising performer & very suitable for our system.",
    2.5: "Very suitable player & could become a promising performer if he changes his position.",
    3: "Very suitable player.",
    3.5: "A player with one desired quality but might become very suitable if he changes his position.",
    4: "Not very suitable but has one or more desired qualities.",
    4.5: "A player who might have a desired quality if he changes his position.",
    5: "Not suitable, no desired qualities & no prospect of changing position.",
}


def validate_player_name(name: str) -> str:
    if not name or not name.strip():
        raise ValueError("Display Name cannot be empty.")
    stripped = name.strip()
    if len(stripped) > 100:
        raise ValueError("Display Name must be 100 characters or fewer.")
    return stripped


def validate_team(team: str) -> str:
    return (team or "").strip()[:100]


def validate_position(position: str) -> str:
    pos = (position or "").strip().upper()
    if pos in VALID_POSITIONS:
        return pos
    if pos in DISPLAY_TO_KEY:
        return DISPLAY_TO_KEY[pos]
    raise ValueError("Invalid position selected.")


def validate_stars(stars) -> float:
    try:
        s = float(stars)
    except (TypeError, ValueError):
        raise ValueError("Rating must be a number.")
    if s not in RATING_OPTIONS:
        raise ValueError("Rating must be 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, or 5.")
    return s


def validate_non_negative_int(val, field_name: str) -> int:
    try:
        v = int(val)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number.")
    if v < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return v


def validate_cards(cards: str) -> str:
    if cards not in CARD_OPTIONS:
        raise ValueError("Received Cards must be None, Yellow, or Red.")
    return cards


def compute_average_stars(reports: list) -> float:
    if not reports:
        return 0.0
    total = sum(r["rating"] for r in reports)
    return round(total / len(reports), 1)


def filter_players_by_position(players: list, position: str) -> list:
    pos = (position or "").strip().upper()
    if not pos:
        return list(players)
    return [p for p in players if p["position"].upper() == pos]


def stars_display(avg: float) -> str:
    filled = round(avg)
    return "★" * filled + "☆" * (5 - filled)
