import re


def format_date_natural(date_str: str | None) -> str:
    if not date_str:
        return ""

    date_str = date_str.strip()
    date_upper = date_str.upper()

    # Dictionnaire de traduction des mois
    months = {
        "JAN": "janvier",
        "FEB": "février",
        "MAR": "mars",
        "APR": "avril",
        "MAY": "mai",
        "JUN": "juin",
        "JUL": "juillet",
        "AUG": "août",
        "SEP": "septembre",
        "OCT": "octobre",
        "NOV": "novembre",
        "DEC": "décembre",
    }

    # BET YYYY AND YYYY (Entre ... et ...)
    match = re.fullmatch(r"BET\s+(\d{4})\s+AND\s+(\d{4})", date_upper)
    if match:
        year1, year2 = match.groups()
        return f"Entre {year1} et {year2}"

    # Préfixes (ABT, EST, BEF, AFT, CAL)
    prefix_map = {
        "ABT": "Vers",
        "EST": "Estimé",
        "BEF": "Avant",
        "AFT": "Après",
        "CAL": "Calculé",
        "VERS": "Vers",
        "AVANT": "Avant",
    }
    for prefix_ged, prefix_fr in prefix_map.items():
        if date_upper.startswith(prefix_ged + " "):
            # Récupère le reste de la date et la formate récursivement
            rest_of_date = date_str[len(prefix_ged) :].strip()
            return f"{prefix_fr} {format_date_natural(rest_of_date)}"

    # Formats de date complets
    # DD MON YYYY (e.g., 23 JUN 1980)
    match = re.fullmatch(r"(\d{1,2})\s+([A-Z]{3})\s+(\d{4})", date_upper)
    if match:
        day, month_abbr, year = match.groups()
        day_int = int(day)
        month_name = months.get(month_abbr)
        if month_name:
            return f"le {day_int}{'er' if day_int == 1 else ''} {month_name} {year}"

    # MON YYYY (e.g., JUN 1980)
    match = re.fullmatch(r"([A-Z]{3})\s+(\d{4})", date_upper)
    if match:
        month_abbr, year = match.groups()
        month_name = months.get(month_abbr)
        if month_name:
            return f"{month_name.capitalize()} {year}"

    # YYYY
    if re.fullmatch(r"\d{4}", date_str):
        return date_str

    return date_str


def parse_date_to_year(date_str: str | None) -> int | None:
    if not date_str:
        return None

    date_str = date_str.strip()

    # Try to find any 4-digit number and assume it's the year
    match = re.search(r"(\d{4})", date_str)
    if match:
        return int(match.group(1))

    return None
