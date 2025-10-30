"""
Tests pour les formatters de présentation web.
"""

import pytest

from src.geneweb.presentation.web.formatters import (
    format_date_natural,
    parse_date_to_year,
)


class TestFormatDateNatural:
    """Tests pour format_date_natural."""

    def test_format_date_empty(self):
        """Test avec une date vide."""
        assert format_date_natural(None) == ""
        assert format_date_natural("") == ""
        assert format_date_natural("   ") == ""

    def test_format_date_between_years(self):
        """Test format BET YYYY AND YYYY."""
        assert format_date_natural("BET 1980 AND 1985") == "Entre 1980 et 1985"
        assert format_date_natural("bet 1900 and 1910") == "Entre 1900 et 1910"
        assert format_date_natural("BET 2000 AND 2020") == "Entre 2000 et 2020"

    def test_format_date_about(self):
        """Test format ABT (About)."""
        assert format_date_natural("ABT 1980") == "Vers 1980"
        assert format_date_natural("ABT JUN 1980") == "Vers Juin 1980"
        assert format_date_natural("ABT 15 JUN 1980") == "Vers le 15 juin 1980"
        assert format_date_natural("VERS 1980") == "Vers 1980"

    def test_format_date_estimated(self):
        """Test format EST (Estimated)."""
        assert format_date_natural("EST 1980") == "Estimé 1980"
        assert format_date_natural("EST JUN 1980") == "Estimé Juin 1980"

    def test_format_date_before(self):
        """Test format BEF (Before)."""
        assert format_date_natural("BEF 1980") == "Avant 1980"
        assert format_date_natural("BEF JUN 1980") == "Avant Juin 1980"
        assert format_date_natural("AVANT 1980") == "Avant 1980"

    def test_format_date_after(self):
        """Test format AFT (After)."""
        assert format_date_natural("AFT 1980") == "Après 1980"
        assert format_date_natural("AFT JUN 1980") == "Après Juin 1980"

    def test_format_date_calculated(self):
        """Test format CAL (Calculated)."""
        assert format_date_natural("CAL 1980") == "Calculé 1980"
        assert format_date_natural("CAL 15 JUN 1980") == "Calculé le 15 juin 1980"

    def test_format_date_full_with_day(self):
        """Test format DD MON YYYY."""
        assert format_date_natural("15 JUN 1980") == "le 15 juin 1980"
        assert format_date_natural("01 JAN 2000") == "le 1er janvier 2000"
        assert format_date_natural("23 DEC 1995") == "le 23 décembre 1995"
        assert format_date_natural("05 MAR 1990") == "le 5 mars 1990"

    def test_format_date_month_year(self):
        """Test format MON YYYY."""
        assert format_date_natural("JUN 1980") == "Juin 1980"
        assert format_date_natural("JAN 2000") == "Janvier 2000"
        assert format_date_natural("DEC 1995") == "Décembre 1995"
        assert format_date_natural("FEB 2020") == "Février 2020"

    def test_format_date_year_only(self):
        """Test format YYYY."""
        assert format_date_natural("1980") == "1980"
        assert format_date_natural("2000") == "2000"
        assert format_date_natural("1850") == "1850"

    def test_format_date_all_months(self):
        """Test tous les mois."""
        months_test = {
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

        for abbr, full_name in months_test.items():
            result = format_date_natural(f"{abbr} 1980")
            assert result == f"{full_name.capitalize()} 1980"

            result_with_day = format_date_natural(f"15 {abbr} 1980")
            assert result_with_day == f"le 15 {full_name} 1980"

    def test_format_date_first_day_of_month(self):
        """Test spécifique pour le 1er du mois."""
        assert format_date_natural("01 JUN 1980") == "le 1er juin 1980"
        assert format_date_natural("1 JUN 1980") == "le 1er juin 1980"

    def test_format_date_unrecognized_format(self):
        """Test avec un format non reconnu."""
        assert format_date_natural("Invalid Date") == "Invalid Date"
        assert format_date_natural("??/??/????") == "??/??/????"
        assert format_date_natural("Unknown") == "Unknown"

    def test_format_date_case_insensitive(self):
        """Test que le format est insensible à la casse."""
        assert format_date_natural("abt 1980") == "Vers 1980"
        assert format_date_natural("ABT 1980") == "Vers 1980"
        assert format_date_natural("Abt 1980") == "Vers 1980"

    def test_format_date_nested_prefixes(self):
        """Test avec des préfixes imbriqués."""
        assert format_date_natural("ABT BEF 1980") == "Vers Avant 1980"


class TestParseDateToYear:
    """Tests pour parse_date_to_year."""

    def test_parse_date_to_year_empty(self):
        """Test avec une date vide."""
        assert parse_date_to_year(None) is None
        assert parse_date_to_year("") is None
        assert parse_date_to_year("   ") is None

    def test_parse_date_to_year_simple(self):
        """Test avec une année simple."""
        assert parse_date_to_year("1980") == 1980
        assert parse_date_to_year("2000") == 2000
        assert parse_date_to_year("1850") == 1850

    def test_parse_date_to_year_with_month(self):
        """Test avec mois et année."""
        assert parse_date_to_year("JUN 1980") == 1980
        assert parse_date_to_year("JAN 2000") == 2000

    def test_parse_date_to_year_full_date(self):
        """Test avec date complète."""
        assert parse_date_to_year("15 JUN 1980") == 1980
        assert parse_date_to_year("01 JAN 2000") == 2000

    def test_parse_date_to_year_with_prefix(self):
        """Test avec des préfixes."""
        assert parse_date_to_year("ABT 1980") == 1980
        assert parse_date_to_year("BEF 1990") == 1990
        assert parse_date_to_year("AFT 2000") == 2000
        assert parse_date_to_year("EST 1975") == 1975

    def test_parse_date_to_year_between(self):
        """Test avec BET...AND (prend la première année trouvée)."""
        assert parse_date_to_year("BET 1980 AND 1985") == 1980

    def test_parse_date_to_year_with_text(self):
        """Test avec du texte contenant une année."""
        assert parse_date_to_year("Born in 1980") == 1980
        assert parse_date_to_year("Year 2000") == 2000

    def test_parse_date_to_year_no_year(self):
        """Test sans année."""
        assert parse_date_to_year("Unknown") is None
        assert parse_date_to_year("No year here") is None
        assert parse_date_to_year("??/??/????") is None

    def test_parse_date_to_year_edge_cases(self):
        """Test avec des cas limites."""
        assert parse_date_to_year("1000") == 1000
        assert parse_date_to_year("9999") == 9999
        assert parse_date_to_year("0001") == 1

    def test_parse_date_to_year_multiple_years(self):
        """Test avec plusieurs années (prend la première)."""
        assert parse_date_to_year("1980 1985 1990") == 1980
        assert parse_date_to_year("From 1980 to 1990") == 1980
