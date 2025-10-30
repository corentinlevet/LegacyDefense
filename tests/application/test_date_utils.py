"""
Tests pour les fonctions utilitaires de gestion des dates.
"""

import pytest
from datetime import datetime

from src.geneweb.application.services import (
    parse_date_for_sorting,
    is_possibly_alive,
    _format_date_for_gedcom,
)


class TestParseDateForSorting:
    """Tests pour la fonction parse_date_for_sorting."""

    def test_empty_date(self):
        """Test avec une date vide ou None."""
        assert parse_date_for_sorting(None) == (9999, 12, 31)
        assert parse_date_for_sorting("") == (9999, 12, 31)
        assert parse_date_for_sorting("   ") == (9999, 12, 31)

    def test_before_date(self):
        """Test avec des dates commençant par 'Avant'."""
        assert parse_date_for_sorting("Avant 1900") == (1899, 12, 31)
        assert parse_date_for_sorting("Before 2000") == (1999, 12, 31)
        assert parse_date_for_sorting("Avant 1850") == (1849, 12, 31)

    def test_estimated_date(self):
        """Test avec des dates estimées."""
        assert parse_date_for_sorting("Estimé 1900") == (1900, 6, 15)
        assert parse_date_for_sorting("About 2000") == (2000, 6, 15)
        assert parse_date_for_sorting("Estimé 1975") == (1975, 6, 15)

    def test_between_dates(self):
        """Test avec des dates 'Entre X et Y'."""
        assert parse_date_for_sorting("Entre 1900 et 1910") == (1900, 1, 1)
        assert parse_date_for_sorting("Between 1950 and 1960") == (1950, 1, 1)
        assert parse_date_for_sorting("Entre 2000 et 2020") == (2000, 1, 1)

    def test_year_only(self):
        """Test avec uniquement une année."""
        assert parse_date_for_sorting("1900") == (1900, 1, 1)
        assert parse_date_for_sorting("2000") == (2000, 1, 1)
        assert parse_date_for_sorting("1850") == (1850, 1, 1)
        assert parse_date_for_sorting("Texte avec 1985 dedans") == (1985, 1, 1)

    def test_full_date_formats(self):
        """Test avec différents formats de dates complètes."""
        # Format DD/MM/YYYY
        assert parse_date_for_sorting("15/06/1980") == (1980, 6, 15)
        assert parse_date_for_sorting("01/01/2000") == (2000, 1, 1)
        
        # Format YYYY-MM-DD
        assert parse_date_for_sorting("1980-06-15") == (1980, 6, 15)
        assert parse_date_for_sorting("2000-01-01") == (2000, 1, 1)

    def test_invalid_date(self):
        """Test avec des dates invalides."""
        assert parse_date_for_sorting("Invalid") == (9999, 12, 31)
        assert parse_date_for_sorting("Not a date") == (9999, 12, 31)
        assert parse_date_for_sorting("???") == (9999, 12, 31)

    def test_edge_cases(self):
        """Test des cas limites."""
        assert parse_date_for_sorting("0") == (0, 1, 1)
        assert parse_date_for_sorting("9999") == (9999, 1, 1)
        assert parse_date_for_sorting("Avant 0001") == (0, 12, 31)


class TestIsPossiblyAlive:
    """Tests pour la fonction is_possibly_alive."""

    def test_person_with_death_date(self):
        """Test avec une date de décès - devrait retourner False."""
        assert is_possibly_alive("1900", "1980") is False
        assert is_possibly_alive("1950", "2020") is False
        assert is_possibly_alive("15/06/1980", "01/01/2023") is False

    def test_person_without_birth_date(self):
        """Test sans date de naissance - devrait retourner False."""
        assert is_possibly_alive(None, None) is False
        assert is_possibly_alive("", None) is False
        assert is_possibly_alive("   ", None) is False

    def test_person_born_recently(self):
        """Test avec une naissance récente - devrait retourner True."""
        current_year = datetime.now().year
        recent_birth = str(current_year - 50)
        assert is_possibly_alive(recent_birth, None) is True
        
        very_recent = str(current_year - 10)
        assert is_possibly_alive(very_recent, None) is True

    def test_person_born_120_years_ago(self):
        """Test avec une naissance il y a exactement 120 ans - limite."""
        current_year = datetime.now().year
        birth_120_years = str(current_year - 120)
        assert is_possibly_alive(birth_120_years, None) is True

    def test_person_born_over_120_years_ago(self):
        """Test avec une naissance il y a plus de 120 ans - devrait retourner False."""
        current_year = datetime.now().year
        old_birth = str(current_year - 121)
        assert is_possibly_alive(old_birth, None) is False
        
        very_old_birth = str(current_year - 150)
        assert is_possibly_alive(very_old_birth, None) is False

    def test_person_with_invalid_birth_date(self):
        """Test avec une date de naissance invalide - devrait retourner False."""
        assert is_possibly_alive("Invalid date", None) is False
        assert is_possibly_alive("???", None) is False

    def test_person_with_estimated_birth_date(self):
        """Test avec une date de naissance estimée."""
        current_year = datetime.now().year
        estimated_birth = f"Estimé {current_year - 60}"
        assert is_possibly_alive(estimated_birth, None) is True
        
        old_estimated = f"Estimé {current_year - 130}"
        assert is_possibly_alive(old_estimated, None) is False


class TestFormatDateForGedcom:
    """Tests pour la fonction _format_date_for_gedcom."""

    def test_none_date(self):
        """Test avec None."""
        assert _format_date_for_gedcom(None) is None

    def test_string_date(self):
        """Test avec une chaîne de caractères."""
        assert _format_date_for_gedcom("1900") == "1900"
        assert _format_date_for_gedcom("15 JUN 1980") == "15 JUN 1980"
        assert _format_date_for_gedcom("Any string") == "Any string"

    def test_date_object(self):
        """Test avec un objet date."""
        from datetime import date
        
        test_date = date(1980, 6, 15)
        result = _format_date_for_gedcom(test_date)
        assert result == "15 JUN 1980"
        
        test_date2 = date(2000, 1, 1)
        result2 = _format_date_for_gedcom(test_date2)
        assert result2 == "01 JAN 2000"

    def test_datetime_object(self):
        """Test avec un objet datetime."""
        from datetime import datetime
        
        test_datetime = datetime(1980, 6, 15, 10, 30, 0)
        result = _format_date_for_gedcom(test_datetime)
        assert result == "15 JUN 1980"
        
        test_datetime2 = datetime(2000, 12, 31, 23, 59, 59)
        result2 = _format_date_for_gedcom(test_datetime2)
        assert result2 == "31 DEC 2000"

    def test_edge_cases_months(self):
        """Test tous les mois de l'année."""
        from datetime import date
        
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        
        for month_idx, month_abbr in enumerate(months, 1):
            test_date = date(2000, month_idx, 15)
            result = _format_date_for_gedcom(test_date)
            assert month_abbr in result
            assert "2000" in result
