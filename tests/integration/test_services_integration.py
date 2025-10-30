"""
Tests d'intégration pour les services et formatters.
"""

import pytest
from datetime import datetime

from src.geneweb.application.services import (
    parse_date_for_sorting,
    is_possibly_alive,
    _format_date_for_gedcom,
)
from src.geneweb.presentation.web.formatters import (
    format_date_natural,
    parse_date_to_year,
)


class TestDateFormattingPipeline:
    """Tests du pipeline complet de formatage de dates."""

    def test_gedcom_to_natural_to_year(self):
        """Test conversion GEDCOM -> naturel -> année."""
        # Format GEDCOM
        gedcom_date = "15 JUN 1980"
        
        # Convertir en format naturel
        natural = format_date_natural(gedcom_date)
        assert "juin" in natural
        assert "1980" in natural
        
        # Extraire l'année
        year = parse_date_to_year(natural)
        assert year == 1980

    def test_python_date_to_gedcom_to_natural(self):
        """Test date Python -> GEDCOM -> naturel."""
        from datetime import date
        
        # Date Python
        py_date = date(1980, 6, 15)
        
        # Convertir en GEDCOM
        gedcom = _format_date_for_gedcom(py_date)
        assert gedcom == "15 JUN 1980"
        
        # Convertir en naturel
        natural = format_date_natural(gedcom)
        assert "juin" in natural

    def test_full_lifecycle_various_formats(self):
        """Test cycle complet avec différents formats."""
        test_cases = [
            ("1980", 1980),
            ("15 JUN 1980", 1980),
            ("ABT 1985", 1985),
            ("BET 1990 AND 2000", 1990),
            ("BEF 1975", 1975),
        ]
        
        for input_date, expected_year in test_cases:
            # Formater
            natural = format_date_natural(input_date)
            
            # Extraire l'année
            year = parse_date_to_year(natural)
            assert year == expected_year, f"Failed for {input_date}"
            
            # Parser pour tri
            sort_tuple = parse_date_for_sorting(natural)
            assert sort_tuple[0] == expected_year or sort_tuple[0] == expected_year - 1


class TestPersonLifeStatus:
    """Tests de détection de statut de vie."""

    def test_recently_born_person(self):
        """Test personne née récemment."""
        current_year = datetime.now().year
        birth_year = current_year - 30
        
        assert is_possibly_alive(str(birth_year), None) is True

    def test_very_old_person(self):
        """Test personne très âgée."""
        current_year = datetime.now().year
        birth_year = current_year - 150
        
        assert is_possibly_alive(str(birth_year), None) is False

    def test_person_at_boundary(self):
        """Test personne à la limite (120 ans)."""
        current_year = datetime.now().year
        birth_year = current_year - 120
        
        # À exactement 120 ans, considérée comme potentiellement vivante
        assert is_possibly_alive(str(birth_year), None) is True
        
        # À 121 ans, considérée comme décédée
        birth_year_121 = current_year - 121
        assert is_possibly_alive(str(birth_year_121), None) is False

    def test_person_with_various_death_formats(self):
        """Test avec différents formats de date de décès."""
        death_formats = [
            "2020",
            "15 JUN 2020",
            "ABT 2020",
            "BEF 2020",
        ]
        
        for death_date in death_formats:
            assert is_possibly_alive("1950", death_date) is False

    def test_person_with_formatted_birth_dates(self):
        """Test avec différents formats de naissance."""
        current_year = datetime.now().year
        recent_year = current_year - 50
        
        birth_formats = [
            str(recent_year),
            f"15 JUN {recent_year}",
            f"ABT {recent_year}",
            f"le 15 juin {recent_year}",
        ]
        
        for birth_date in birth_formats:
            result = is_possibly_alive(birth_date, None)
            assert result is True, f"Failed for {birth_date}"


class TestDateSorting:
    """Tests de tri de dates."""

    def test_sort_simple_years(self):
        """Test tri d'années simples."""
        dates = ["2000", "1980", "1990", "1970"]
        sorted_dates = sorted(dates, key=lambda d: parse_date_for_sorting(d))
        
        assert sorted_dates == ["1970", "1980", "1990", "2000"]

    def test_sort_mixed_formats(self):
        """Test tri de formats mélangés."""
        dates = [
            "2000",
            "15 JUN 1980",
            "ABT 1990",
            "BEF 1970",
        ]
        
        sorted_dates = sorted(dates, key=lambda d: parse_date_for_sorting(d))
        
        # Vérifier l'ordre général (les années)
        years = [parse_date_for_sorting(d)[0] for d in sorted_dates]
        assert years[0] < years[1] < years[2] < years[3]

    def test_sort_with_invalid_dates(self):
        """Test tri avec dates invalides."""
        dates = ["2000", "Invalid", "1980", "???", "1990"]
        sorted_dates = sorted(dates, key=lambda d: parse_date_for_sorting(d))
        
        # Les dates valides doivent venir en premier
        valid_dates = [d for d in sorted_dates if d in ["1980", "1990", "2000"]]
        assert valid_dates == ["1980", "1990", "2000"]

    def test_sort_estimated_dates(self):
        """Test tri de dates estimées."""
        dates = [
            "Estimé 2000",
            "Estimé 1980",
            "Estimé 1990",
        ]
        
        sorted_dates = sorted(dates, key=lambda d: parse_date_for_sorting(d))
        
        # Vérifier l'ordre
        assert "1980" in sorted_dates[0]
        assert "1990" in sorted_dates[1]
        assert "2000" in sorted_dates[2]

    def test_sort_before_dates(self):
        """Test tri de dates 'avant'."""
        dates = [
            "Avant 2000",
            "Avant 1980",
            "Avant 1990",
        ]
        
        sorted_dates = sorted(dates, key=lambda d: parse_date_for_sorting(d))
        
        # Les dates 'avant' utilisent année - 1
        years = [parse_date_for_sorting(d)[0] for d in sorted_dates]
        assert years == [1979, 1989, 1999]


class TestFormatConsistency:
    """Tests de cohérence entre les fonctions de formatage."""

    def test_format_round_trip_consistency(self):
        """Test cohérence aller-retour."""
        test_dates = [
            "1980",
            "15 JUN 1980",
            "JUN 1980",
        ]
        
        for date in test_dates:
            formatted = format_date_natural(date)
            year = parse_date_to_year(formatted)
            assert year == 1980

    def test_gedcom_format_consistency(self):
        """Test cohérence format GEDCOM."""
        from datetime import date
        
        test_date = date(1980, 6, 15)
        gedcom = _format_date_for_gedcom(test_date)
        
        # Devrait pouvoir parser ce format
        year = parse_date_to_year(gedcom)
        assert year == 1980

    def test_empty_dates_consistency(self):
        """Test cohérence avec dates vides."""
        # Toutes ces fonctions doivent gérer None/vide
        assert format_date_natural(None) == ""
        assert parse_date_to_year(None) is None
        assert parse_date_for_sorting(None) == (9999, 12, 31)
        assert is_possibly_alive(None, None) is False

    def test_prefix_handling_consistency(self):
        """Test cohérence de gestion des préfixes."""
        prefixes = ["ABT", "EST", "BEF", "AFT", "CAL"]
        
        for prefix in prefixes:
            date_str = f"{prefix} 1980"
            
            # format_date_natural devrait traduire le préfixe
            formatted = format_date_natural(date_str)
            assert formatted != date_str
            
            # parse_date_to_year devrait extraire l'année
            year = parse_date_to_year(date_str)
            assert year == 1980


class TestEdgeCasesCombinations:
    """Tests de combinaisons de cas limites."""

    def test_leap_year_dates(self):
        """Test dates d'année bissextile."""
        leap_dates = [
            "29 FEB 2000",
            "29 FEB 2020",
        ]
        
        for date_str in leap_dates:
            formatted = format_date_natural(date_str)
            assert "février" in formatted
            assert "29" in formatted

    def test_year_boundaries(self):
        """Test années limites."""
        boundary_years = ["0001", "9999", "1000", "2000"]
        
        for year in boundary_years:
            formatted = format_date_natural(year)
            assert year in formatted
            
            parsed_year = parse_date_to_year(year)
            assert parsed_year == int(year)

    def test_month_boundaries(self):
        """Test mois limites (janvier et décembre)."""
        dates = [
            "01 JAN 2000",
            "31 DEC 2000",
        ]
        
        for date_str in dates:
            formatted = format_date_natural(date_str)
            year = parse_date_to_year(formatted)
            assert year == 2000

    def test_unicode_in_dates(self):
        """Test caractères Unicode dans les dates."""
        # Les mois français ont des accents
        date_str = "15 FEB 1980"
        formatted = format_date_natural(date_str)
        assert "février" in formatted  # avec accent

    def test_very_old_dates(self):
        """Test dates très anciennes."""
        old_dates = ["100", "500", "1000"]
        
        for date_str in old_dates:
            year = parse_date_to_year(date_str)
            assert year == int(date_str)
            
            # Personne née si vieille est forcément décédée
            assert is_possibly_alive(date_str, None) is False

    def test_future_dates(self):
        """Test dates futures."""
        current_year = datetime.now().year
        future_year = current_year + 10
        
        # Une personne 'née' dans le futur est considérée comme vivante
        # (même si c'est une erreur de données)
        result = is_possibly_alive(str(future_year), None)
        # L'âge sera négatif, donc <= 120
        assert result is True


class TestRealWorldScenarios:
    """Tests de scénarios réels."""

    def test_historical_person(self):
        """Test personne historique."""
        # Napoléon Bonaparte
        birth = "15 AUG 1769"
        death = "05 MAY 1821"
        
        assert is_possibly_alive(birth, death) is False
        
        birth_year = parse_date_to_year(birth)
        assert birth_year == 1769

    def test_recent_person(self):
        """Test personne récente."""
        current_year = datetime.now().year
        birth = f"{current_year - 40}"
        
        assert is_possibly_alive(birth, None) is True

    def test_genealogy_dates_sequence(self):
        """Test séquence de dates généalogiques."""
        # Trois générations
        grand_parent_birth = "1920"
        parent_birth = "1950"
        child_birth = "1980"
        
        dates = [grand_parent_birth, parent_birth, child_birth]
        sorted_dates = sorted(dates, key=lambda d: parse_date_for_sorting(d))
        
        assert sorted_dates == ["1920", "1950", "1980"]

    def test_marriage_dates(self):
        """Test dates de mariage."""
        marriage_dates = [
            "15 JUN 1990",
            "ABT 1995",
            "BEF 2000",
        ]
        
        for date_str in marriage_dates:
            formatted = format_date_natural(date_str)
            assert formatted != ""
            
            year = parse_date_to_year(formatted)
            assert year is not None
            assert 1990 <= year <= 2000

    def test_incomplete_dates(self):
        """Test dates incomplètes."""
        incomplete = [
            "JUN 1980",  # Mois et année seulement
            "1980",      # Année seulement
        ]
        
        for date_str in incomplete:
            formatted = format_date_natural(date_str)
            assert "1980" in formatted
            
            year = parse_date_to_year(formatted)
            assert year == 1980
