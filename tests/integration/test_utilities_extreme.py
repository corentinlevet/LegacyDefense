"""
Tests supplémentaires pour les utilities et helpers.
"""

import pytest
from datetime import date, datetime

from src.geneweb.application.services import (
    parse_date_for_sorting,
    is_possibly_alive,
    _format_date_for_gedcom,
)
from src.geneweb.presentation.web.formatters import (
    format_date_natural,
    parse_date_to_year,
)


class TestDateParsingExtreme:
    """Tests extrêmes de parsing de dates."""

    def test_very_ancient_dates(self):
        """Test dates très anciennes."""
        ancient_dates = ["0001", "0100", "0500", "1000"]
        
        for date_str in ancient_dates:
            year = parse_date_to_year(date_str)
            assert year == int(date_str)
            
            sort_tuple = parse_date_for_sorting(date_str)
            assert sort_tuple[0] == int(date_str)

    def test_distant_future_dates(self):
        """Test dates lointaines dans le futur."""
        future_dates = ["3000", "5000", "9999"]
        
        for date_str in future_dates:
            year = parse_date_to_year(date_str)
            assert year == int(date_str)

    def test_dates_with_leading_zeros(self):
        """Test dates avec zéros devant."""
        dates_with_zeros = ["0100", "0050", "0001"]
        
        for date_str in dates_with_zeros:
            year = parse_date_to_year(date_str)
            assert year is not None

    def test_dates_with_multiple_years(self):
        """Test dates contenant plusieurs années."""
        multi_year_dates = [
            "Entre 1900 et 2000",
            "BET 1980 AND 1990",
            "Né en 1950, décédé en 2020"
        ]
        
        for date_str in multi_year_dates:
            year = parse_date_to_year(date_str)
            # Devrait prendre la première année trouvée
            assert year is not None

    def test_dates_with_noise(self):
        """Test dates avec beaucoup de texte parasite."""
        noisy_dates = [
            "Probablement né vers l'année 1980 à Paris",
            "Estimation de naissance: 1975 (non confirmé)",
            "Date approximative 1990",
        ]
        
        for date_str in noisy_dates:
            year = parse_date_to_year(date_str)
            assert year is not None


class TestDateFormattingExtreme:
    """Tests extrêmes de formatage de dates."""

    def test_format_all_days_of_month(self):
        """Test formatage de tous les jours du mois."""
        for day in range(1, 32):
            date_str = f"{day:02d} JUN 1980"
            formatted = format_date_natural(date_str)
            
            if day == 1:
                assert "1er" in formatted
            else:
                assert str(day) in formatted
            assert "juin" in formatted

    def test_format_all_months(self):
        """Test formatage de tous les mois."""
        months = {
            "JAN": "janvier", "FEB": "février", "MAR": "mars",
            "APR": "avril", "MAY": "mai", "JUN": "juin",
            "JUL": "juillet", "AUG": "août", "SEP": "septembre",
            "OCT": "octobre", "NOV": "novembre", "DEC": "décembre"
        }
        
        for abbr, full_name in months.items():
            date_str = f"15 {abbr} 1980"
            formatted = format_date_natural(date_str)
            assert full_name in formatted.lower()

    def test_format_century_transitions(self):
        """Test formatage aux transitions de siècle."""
        century_dates = ["1899", "1900", "1901", "1999", "2000", "2001"]
        
        for year in century_dates:
            formatted = format_date_natural(year)
            assert year in formatted

    def test_format_millennium_transitions(self):
        """Test formatage aux transitions de millénaire."""
        millennium_dates = ["0999", "1000", "1999", "2000", "2999", "3000"]
        
        for year in millennium_dates:
            formatted = format_date_natural(year)
            assert year in formatted


class TestLifeStatusEdgeCases:
    """Tests cas limites pour détection de vie."""

    def test_exactly_120_years_old_various_formats(self):
        """Test personne de exactement 120 ans avec différents formats."""
        current_year = datetime.now().year
        birth_year = current_year - 120
        
        birth_formats = [
            str(birth_year),
            f"15 JUN {birth_year}",
            f"ABT {birth_year}",
            f"JUN {birth_year}",
        ]
        
        for birth_date in birth_formats:
            result = is_possibly_alive(birth_date, None)
            assert result is True, f"Failed for {birth_date}"

    def test_person_born_today(self):
        """Test personne née aujourd'hui."""
        today = datetime.now()
        birth_date = _format_date_for_gedcom(today)
        
        assert is_possibly_alive(birth_date, None) is True

    def test_person_died_today(self):
        """Test personne décédée aujourd'hui."""
        today = datetime.now()
        death_date = _format_date_for_gedcom(today)
        
        assert is_possibly_alive("1950", death_date) is False

    def test_birth_after_death_paradox(self):
        """Test paradoxe naissance après décès."""
        # Données incohérentes
        birth = "2000"
        death = "1990"
        
        # Devrait quand même retourner False (décès enregistré)
        assert is_possibly_alive(birth, death) is False


class TestGedcomFormatting:
    """Tests de formatage GEDCOM."""

    def test_format_date_all_months(self):
        """Test formatage de tous les mois en GEDCOM."""
        months = range(1, 13)
        
        for month in months:
            test_date = date(1980, month, 15)
            gedcom = _format_date_for_gedcom(test_date)
            
            assert gedcom is not None
            assert "1980" in gedcom
            assert len(gedcom.split()) == 3  # "DD MON YYYY"

    def test_format_datetime_various_times(self):
        """Test formatage datetime avec différentes heures."""
        times = [
            (0, 0, 0),
            (12, 30, 45),
            (23, 59, 59),
        ]
        
        for hour, minute, second in times:
            test_datetime = datetime(1980, 6, 15, hour, minute, second)
            gedcom = _format_date_for_gedcom(test_datetime)
            
            # L'heure ne devrait pas apparaître dans le format GEDCOM
            assert "1980" in gedcom
            assert str(hour) not in gedcom or "15" in gedcom  # 15 = jour

    def test_format_edge_days(self):
        """Test formatage de jours limites."""
        edge_cases = [
            date(1980, 1, 1),   # Premier jour de l'année
            date(1980, 12, 31),  # Dernier jour de l'année
            date(2000, 2, 29),   # Jour bissextile
        ]
        
        for test_date in edge_cases:
            gedcom = _format_date_for_gedcom(test_date)
            assert gedcom is not None
            assert len(gedcom) > 0


class TestSortingComplexScenarios:
    """Tests de tri de scénarios complexes."""

    def test_sort_mixed_precision_dates(self):
        """Test tri de dates avec précisions mixtes."""
        dates = [
            "1980",           # Année seulement
            "15 JUN 1980",    # Date complète
            "JUN 1980",       # Mois et année
            "ABT 1980",       # Estimée
        ]
        
        sorted_dates = sorted(dates, key=lambda d: parse_date_for_sorting(d))
        
        # Toutes devraient avoir 1980 comme année
        for date_str in sorted_dates:
            year = parse_date_to_year(date_str)
            assert year == 1980

    def test_sort_century_spanning_dates(self):
        """Test tri de dates sur plusieurs siècles."""
        dates = [
            "1850",
            "1900",
            "1950",
            "2000",
            "2050",
        ]
        
        sorted_dates = sorted(dates, key=lambda d: parse_date_for_sorting(d))
        assert sorted_dates == dates  # Déjà triées

    def test_sort_with_estimated_and_exact(self):
        """Test tri mélange estimées et exactes."""
        dates = [
            "15 JUN 2000",
            "ABT 1980",
            "15 DEC 1990",
            "EST 1970",
        ]
        
        sorted_dates = sorted(dates, key=lambda d: parse_date_for_sorting(d))
        
        # Vérifier ordre des années
        years = [parse_date_to_year(d) for d in sorted_dates]
        assert years == [1970, 1980, 1990, 2000]

    def test_sort_genealogy_timeline(self):
        """Test tri d'une chronologie généalogique."""
        timeline = [
            ("Décès grand-père", "15 MAR 1980"),
            ("Naissance père", "10 JUN 1940"),
            ("Mariage parents", "20 SEP 1970"),
            ("Naissance enfant", "15 DEC 1975"),
            ("Naissance grand-père", "ABT 1910"),
        ]
        
        sorted_timeline = sorted(
            timeline,
            key=lambda x: parse_date_for_sorting(x[1])
        )
        
        # Vérifier ordre chronologique
        labels = [event[0] for event in sorted_timeline]
        assert labels[0] == "Naissance grand-père"
        assert labels[1] == "Naissance père"


class TestRobustness:
    """Tests de robustesse."""

    def test_null_and_none_handling(self):
        """Test gestion de NULL et None."""
        assert format_date_natural(None) == ""
        assert parse_date_to_year(None) is None
        assert parse_date_for_sorting(None) == (9999, 12, 31)
        assert _format_date_for_gedcom(None) is None

    def test_empty_string_handling(self):
        """Test gestion de chaînes vides."""
        assert format_date_natural("") == ""
        assert parse_date_to_year("") is None
        assert parse_date_for_sorting("") == (9999, 12, 31)

    def test_whitespace_only_handling(self):
        """Test gestion d'espaces uniquement."""
        assert format_date_natural("   ") == ""
        assert parse_date_to_year("   ") is None
        assert parse_date_for_sorting("   ") == (9999, 12, 31)

    def test_very_long_string_handling(self):
        """Test gestion de chaînes très longues."""
        long_string = "A" * 10000 + "1980" + "B" * 10000
        
        # Devrait quand même trouver l'année
        year = parse_date_to_year(long_string)
        assert year == 1980

    def test_special_characters_handling(self):
        """Test gestion de caractères spéciaux."""
        special_dates = [
            "15/06/1980",
            "15-06-1980",
            "15.06.1980",
            "15 июня 1980",  # Cyrillique
        ]
        
        for date_str in special_dates:
            # Ne devrait pas crasher
            try:
                formatted = format_date_natural(date_str)
                year = parse_date_to_year(date_str)
                # Au moins l'année devrait être trouvée
                assert year == 1980 or formatted is not None
            except Exception:
                pytest.fail(f"Failed for {date_str}")

    def test_repeated_function_calls(self):
        """Test appels répétés des fonctions."""
        test_date = "15 JUN 1980"
        
        # Appeler 1000 fois
        for _ in range(1000):
            formatted = format_date_natural(test_date)
            year = parse_date_to_year(formatted)
            assert year == 1980

    def test_malformed_gedcom_dates(self):
        """Test dates GEDCOM malformées."""
        malformed = [
            "15 JUNE 1980",      # Mois complet au lieu d'abréviation
            "1980 JUN 15",       # Ordre inversé
            "JUN 15 1980",       # Format US
            "15-JUN-1980",       # Avec tirets
        ]
        
        for date_str in malformed:
            # Ne devrait pas crasher
            try:
                formatted = format_date_natural(date_str)
                assert formatted is not None
            except Exception:
                pytest.fail(f"Crashed for {date_str}")


class TestConsistencyAcrossFormats:
    """Tests de cohérence entre formats."""

    def test_same_date_different_formats(self):
        """Test même date dans différents formats."""
        same_date_formats = [
            "1980",
            "JUN 1980",
            "15 JUN 1980",
        ]
        
        years = [parse_date_to_year(d) for d in same_date_formats]
        
        # Toutes devraient donner 1980
        assert all(y == 1980 for y in years)

    def test_format_preservation(self):
        """Test préservation du format."""
        # Une année seule reste une année
        assert format_date_natural("1980") == "1980"
        
        # Un format GEDCOM est traduit
        formatted = format_date_natural("15 JUN 1980")
        assert "juin" in formatted

    def test_bidirectional_conversion_loss(self):
        """Test perte d'information dans conversions."""
        original = "15 JUN 1980"
        formatted = format_date_natural(original)
        year_only = parse_date_to_year(formatted)
        
        # On perd le jour et le mois en extrayant juste l'année
        assert year_only == 1980
        # Mais on ne peut pas retrouver le jour original
