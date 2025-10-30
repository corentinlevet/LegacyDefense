"""
Tests avancés pour les formatters - cas non couverts.
"""

import pytest

from src.geneweb.presentation.web.formatters import (
    format_date_natural,
    parse_date_to_year,
)


class TestFormatDateNaturalAdvanced:
    """Tests avancés pour format_date_natural avec cas edge."""

    def test_format_date_with_extra_spaces(self):
        """Test avec des espaces supplémentaires."""
        assert format_date_natural("  BET 1980 AND 1985  ") == "Entre 1980 et 1985"
        assert format_date_natural("  ABT 1980  ") == "Vers 1980"
        assert format_date_natural("  15 JUN 1980  ") == "le 15 juin 1980"

    def test_format_date_nested_prefixes(self):
        """Test avec des préfixes imbriqués."""
        # ABT suivi d'un autre format
        result = format_date_natural("ABT 23 JUN 1980")
        assert "Vers" in result
        assert "juin" in result
        assert "1980" in result

    def test_format_date_lowercase_input(self):
        """Test avec des entrées en minuscules."""
        assert format_date_natural("bet 1980 and 1985") == "Entre 1980 et 1985"
        assert format_date_natural("abt 1980") == "Vers 1980"
        assert format_date_natural("bef 1980") == "Avant 1980"

    def test_format_date_mixed_case(self):
        """Test avec des casses mixtes."""
        assert format_date_natural("BeT 1980 AnD 1985") == "Entre 1980 et 1985"
        assert format_date_natural("AbT 1980") == "Vers 1980"

    def test_format_date_unknown_month(self):
        """Test avec un mois inconnu/invalide."""
        # Les mois non reconnus ne devraient pas causer d'erreur
        result = format_date_natural("15 XXX 1980")
        assert result == "15 XXX 1980"  # Retourne tel quel
        
        result2 = format_date_natural("XXX 1980")
        assert result2 == "XXX 1980"

    def test_format_date_invalid_day(self):
        """Test avec un jour invalide."""
        result = format_date_natural("99 JUN 1980")
        # Devrait retourner tel quel si le pattern ne match pas
        assert "1980" in result

    def test_format_date_year_boundaries(self):
        """Test avec des années limites."""
        assert format_date_natural("0001") == "0001"
        assert format_date_natural("9999") == "9999"
        assert format_date_natural("1 JAN 0001") == "le 1er janvier 0001"
        assert format_date_natural("31 DEC 9999") == "le 31 décembre 9999"

    def test_format_date_all_prefixes(self):
        """Test tous les préfixes supportés."""
        prefixes = [
            ("ABT", "Vers"),
            ("EST", "Estimé"),
            ("BEF", "Avant"),
            ("AFT", "Après"),
            ("CAL", "Calculé"),
            ("VERS", "Vers"),
            ("AVANT", "Avant"),
        ]
        
        for ged_prefix, fr_prefix in prefixes:
            result = format_date_natural(f"{ged_prefix} 1980")
            assert result.startswith(fr_prefix), f"Failed for {ged_prefix}"
            assert "1980" in result

    def test_format_date_single_digit_day(self):
        """Test avec un jour à un seul chiffre."""
        assert format_date_natural("1 JAN 2000") == "le 1er janvier 2000"
        assert format_date_natural("2 JAN 2000") == "le 2 janvier 2000"
        assert format_date_natural("9 DEC 1999") == "le 9 décembre 1999"

    def test_format_date_double_digit_day(self):
        """Test avec des jours à deux chiffres."""
        assert format_date_natural("10 JAN 2000") == "le 10 janvier 2000"
        assert format_date_natural("31 DEC 1999") == "le 31 décembre 1999"

    def test_format_date_not_matching_any_pattern(self):
        """Test avec des formats qui ne matchent aucun pattern."""
        # Devrait retourner la chaîne originale
        assert format_date_natural("Une date bizarre") == "Une date bizarre"
        assert format_date_natural("12345") == "12345"
        assert format_date_natural("INVALID DATE") == "INVALID DATE"


class TestParseDateToYearAdvanced:
    """Tests avancés pour parse_date_to_year."""

    def test_parse_empty_dates(self):
        """Test avec des dates vides."""
        assert parse_date_to_year(None) is None
        assert parse_date_to_year("") is None
        assert parse_date_to_year("   ") is None

    def test_parse_simple_year(self):
        """Test avec une année simple."""
        assert parse_date_to_year("1980") == 1980
        assert parse_date_to_year("2000") == 2000
        assert parse_date_to_year("1850") == 1850

    def test_parse_year_with_prefix(self):
        """Test avec un préfixe avant l'année."""
        assert parse_date_to_year("ABT 1980") == 1980
        assert parse_date_to_year("Vers 1985") == 1985
        assert parse_date_to_year("Avant 1990") == 1990

    def test_parse_year_with_suffix(self):
        """Test avec du texte après l'année."""
        assert parse_date_to_year("1980 environ") == 1980
        assert parse_date_to_year("L'année 2000") == 2000

    def test_parse_full_date(self):
        """Test avec une date complète."""
        assert parse_date_to_year("15 JUN 1980") == 1980
        assert parse_date_to_year("01 JAN 2000") == 2000
        assert parse_date_to_year("le 15 juin 1980") == 1980

    def test_parse_between_dates(self):
        """Test avec 'entre X et Y' - devrait prendre la première année."""
        assert parse_date_to_year("BET 1980 AND 1985") == 1980
        assert parse_date_to_year("Entre 1900 et 1950") == 1900

    def test_parse_no_year(self):
        """Test sans année dans la chaîne."""
        assert parse_date_to_year("Invalid") is None
        assert parse_date_to_year("No year here") is None
        assert parse_date_to_year("ABC") is None

    def test_parse_year_boundaries(self):
        """Test avec des années limites."""
        assert parse_date_to_year("0001") == 1
        assert parse_date_to_year("9999") == 9999
        assert parse_date_to_year("0000") == 0

    def test_parse_multiple_years(self):
        """Test avec plusieurs années - devrait prendre la première."""
        assert parse_date_to_year("Entre 1900 et 2000") == 1900
        assert parse_date_to_year("1980 ou 1985") == 1980

    def test_parse_year_with_special_chars(self):
        """Test avec des caractères spéciaux autour de l'année."""
        assert parse_date_to_year("(1980)") == 1980
        assert parse_date_to_year("[2000]") == 2000
        assert parse_date_to_year("~1990") == 1990
        assert parse_date_to_year("±1985") == 1985

    def test_parse_three_digit_number(self):
        """Test avec un nombre à 3 chiffres - ne devrait pas matcher."""
        # Le regex cherche exactement 4 chiffres
        assert parse_date_to_year("123") is None
        assert parse_date_to_year("999") is None

    def test_parse_five_digit_number(self):
        """Test avec un nombre à 5 chiffres - devrait prendre les 4 premiers."""
        # Le regex cherche 4 chiffres consécutifs
        result = parse_date_to_year("12345")
        assert result == 1234 or result == 2345

    def test_parse_formatted_dates(self):
        """Test avec des dates formatées en français."""
        assert parse_date_to_year("le 15 juin 1980") == 1980
        assert parse_date_to_year("Juin 1980") == 1980
        assert parse_date_to_year("le 1er janvier 2000") == 2000


class TestFormattersIntegration:
    """Tests d'intégration entre les deux fonctions."""

    def test_format_then_parse(self):
        """Test formatage puis parsing."""
        # Formater une date
        formatted = format_date_natural("15 JUN 1980")
        # Parser l'année de la date formatée
        year = parse_date_to_year(formatted)
        assert year == 1980

    def test_round_trip_various_formats(self):
        """Test aller-retour avec différents formats."""
        test_dates = [
            ("1980", 1980),
            ("ABT 1985", 1985),
            ("15 JUN 1990", 1990),
            ("BET 2000 AND 2010", 2000),
        ]
        
        for date_input, expected_year in test_dates:
            formatted = format_date_natural(date_input)
            year = parse_date_to_year(formatted)
            assert year == expected_year, f"Failed for {date_input}"

    def test_consistency_empty_dates(self):
        """Test cohérence avec dates vides."""
        formatted = format_date_natural(None)
        assert formatted == ""
        
        year = parse_date_to_year(None)
        assert year is None
        
        year2 = parse_date_to_year(formatted)
        assert year2 is None
