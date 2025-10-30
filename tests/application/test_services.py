from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from src.geneweb.application.services import (
    ApplicationService,
    GenealogyDetails,
    _format_date_for_gedcom,
    is_possibly_alive,
    parse_date_for_sorting,
)


# Mock SessionLocal for database interactions
@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy session."""
    session = MagicMock()
    return session


# Mock SQLGenealogyRepository
@pytest.fixture
def mock_genealogy_repo():
    repo = MagicMock()
    mock_genealogy = MagicMock()
    mock_genealogy.id = 1
    mock_genealogy.name = "test_genealogy"
    repo.get_by_name.return_value = mock_genealogy
    return repo


# ApplicationService instance with mocked dependencies
@pytest.fixture
def app_service(mock_genealogy_repo):
    """Provides an ApplicationService instance with mocked dependencies."""
    return ApplicationService(genealogy_repo=mock_genealogy_repo)


# Basic ApplicationService tests
@pytest.mark.asyncio
async def test_get_genealogy_details(app_service, mock_genealogy_repo):
    """Test get_genealogy_details returns correct data."""
    # Arrange
    mock_genealogy_repo.count_persons.return_value = 123

    # Act
    details = await app_service.get_genealogy_details("test_genealogy")

    # Assert
    assert isinstance(details, GenealogyDetails)
    assert details.name == "test_genealogy"
    assert details.person_count == 123
    mock_genealogy_repo.get_by_name.assert_called_once_with("test_genealogy")
    mock_genealogy_repo.count_persons.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_genealogy_details_not_found(app_service, mock_genealogy_repo):
    """Test get_genealogy_details when genealogy is not found."""
    # Arrange
    mock_genealogy_repo.get_by_name.return_value = None

    # Act
    details = await app_service.get_genealogy_details("unknown_genealogy")

    # Assert
    assert details is None
    mock_genealogy_repo.get_by_name.assert_called_once_with("unknown_genealogy")
    mock_genealogy_repo.count_persons.assert_not_called()


@pytest.mark.asyncio
async def test_get_first_names(app_service, mock_genealogy_repo):
    """Test get_first_names."""
    mock_genealogy_repo.get_first_names.return_value = ["John", "Jane", "Peter"]

    result = await app_service.get_first_names("test_genealogy")

    assert result == ["John", "Jane", "Peter"]
    mock_genealogy_repo.get_by_name.assert_called_once_with("test_genealogy")
    mock_genealogy_repo.get_first_names.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_first_names_not_found(app_service, mock_genealogy_repo):
    """Test get_first_names when genealogy not found."""
    mock_genealogy_repo.get_by_name.return_value = None

    result = await app_service.get_first_names("unknown")

    assert result is None


@pytest.mark.asyncio
async def test_get_last_names(app_service, mock_genealogy_repo):
    """Test get_last_names."""
    mock_genealogy_repo.get_last_names.return_value = ["Doe", "Smith"]

    result = await app_service.get_last_names("test_genealogy")

    assert result == ["Doe", "Smith"]
    mock_genealogy_repo.get_last_names.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_last_names_not_found(app_service, mock_genealogy_repo):
    """Test get_last_names when genealogy not found."""
    mock_genealogy_repo.get_by_name.return_value = None

    result = await app_service.get_last_names("unknown")

    assert result is None


@pytest.mark.asyncio
async def test_get_places(app_service, mock_genealogy_repo):
    """Test get_places."""
    mock_genealogy_repo.get_places.return_value = ["Paris", "London"]

    result = await app_service.get_places("test_genealogy")

    assert result == ["Paris", "London"]
    mock_genealogy_repo.get_places.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_places_not_found(app_service, mock_genealogy_repo):
    """Test get_places when genealogy not found."""
    mock_genealogy_repo.get_by_name.return_value = None

    result = await app_service.get_places("unknown")

    assert result is None


@pytest.mark.asyncio
async def test_get_occupations(app_service, mock_genealogy_repo):
    """Test get_occupations."""
    mock_genealogy_repo.get_occupations.return_value = ["Engineer", "Doctor"]

    result = await app_service.get_occupations("test_genealogy")

    assert result == ["Engineer", "Doctor"]
    mock_genealogy_repo.get_occupations.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_occupations_not_found(app_service, mock_genealogy_repo):
    """Test get_occupations when genealogy not found."""
    mock_genealogy_repo.get_by_name.return_value = None

    result = await app_service.get_occupations("unknown")

    assert result is None


@pytest.mark.asyncio
async def test_get_sources(app_service, mock_genealogy_repo):
    """Test get_sources."""
    mock_genealogy_repo.get_sources.return_value = ["Source1", "Source2"]

    result = await app_service.get_sources("test_genealogy")

    assert result == ["Source1", "Source2"]
    mock_genealogy_repo.get_sources.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_sources_not_found(app_service, mock_genealogy_repo):
    """Test get_sources when genealogy not found."""
    mock_genealogy_repo.get_by_name.return_value = None

    result = await app_service.get_sources("unknown")

    assert result is None


# Tests for utility functions
def test_format_date_for_gedcom_with_date():
    """Test _format_date_for_gedcom with date object."""
    d = date(1990, 5, 15)
    result = _format_date_for_gedcom(d)
    assert result == "15 MAY 1990"


def test_format_date_for_gedcom_with_datetime():
    """Test _format_date_for_gedcom with datetime object."""
    d = datetime(1990, 5, 15, 10, 30)
    result = _format_date_for_gedcom(d)
    assert result == "15 MAY 1990"


def test_format_date_for_gedcom_with_string():
    """Test _format_date_for_gedcom with string."""
    d = "15/05/1990"
    result = _format_date_for_gedcom(d)
    assert result == "15/05/1990"


def test_format_date_for_gedcom_with_none():
    """Test _format_date_for_gedcom with None."""
    result = _format_date_for_gedcom(None)
    assert result is None


def test_format_date_for_gedcom_with_exception():
    """Test _format_date_for_gedcom with object that raises exception."""

    class BadDate:
        def strftime(self, fmt):
            raise ValueError("Bad date")

    result = _format_date_for_gedcom(BadDate())
    assert isinstance(result, str)


def test_parse_date_for_sorting_none():
    """Test parse_date_for_sorting with None."""
    result = parse_date_for_sorting(None)
    assert result == (9999, 12, 31)


def test_parse_date_for_sorting_empty():
    """Test parse_date_for_sorting with empty string."""
    result = parse_date_for_sorting("")
    assert result == (9999, 12, 31)


def test_parse_date_for_sorting_avant():
    """Test parse_date_for_sorting with 'Avant' prefix."""
    result = parse_date_for_sorting("Avant 1950")
    assert result == (1949, 12, 31)


def test_parse_date_for_sorting_before():
    """Test parse_date_for_sorting with 'Before' prefix."""
    result = parse_date_for_sorting("Before 1950")
    assert result == (1949, 12, 31)


def test_parse_date_for_sorting_estime():
    """Test parse_date_for_sorting with 'Estimé' prefix."""
    result = parse_date_for_sorting("Estimé 1950")
    assert result == (1950, 6, 15)


def test_parse_date_for_sorting_about():
    """Test parse_date_for_sorting with 'About' prefix."""
    result = parse_date_for_sorting("About 1950")
    assert result == (1950, 6, 15)


def test_parse_date_for_sorting_entre():
    """Test parse_date_for_sorting with 'Entre' prefix."""
    result = parse_date_for_sorting("Entre 1950 et 1960")
    assert result == (1950, 1, 1)


def test_parse_date_for_sorting_between():
    """Test parse_date_for_sorting with 'Between' prefix."""
    result = parse_date_for_sorting("Between 1950 and 1960")
    assert result == (1950, 1, 1)


def test_parse_date_for_sorting_full_date_slash():
    """Test parse_date_for_sorting with full date DD/MM/YYYY."""
    result = parse_date_for_sorting("15/05/1990")
    assert result == (1990, 5, 15)


def test_parse_date_for_sorting_full_date_iso():
    """Test parse_date_for_sorting with ISO date."""
    result = parse_date_for_sorting("1990-05-15")
    assert result == (1990, 5, 15)


def test_parse_date_for_sorting_month_name_full():
    """Test parse_date_for_sorting with full month name."""
    result = parse_date_for_sorting("15 May 1990")
    assert result == (1990, 5, 15)


def test_parse_date_for_sorting_month_name_abbr():
    """Test parse_date_for_sorting with abbreviated month name."""
    result = parse_date_for_sorting("15 MAY 1990")
    assert result == (1990, 5, 15)


def test_parse_date_for_sorting_year_only():
    """Test parse_date_for_sorting with year only."""
    result = parse_date_for_sorting("1990")
    assert result == (1990, 1, 1)


def test_parse_date_for_sorting_invalid():
    """Test parse_date_for_sorting with invalid date."""
    result = parse_date_for_sorting("not a date")
    assert result == (9999, 12, 31)


def test_is_possibly_alive_with_death_date():
    """Test is_possibly_alive when death date exists."""
    result = is_possibly_alive("01/01/1950", "01/01/2020")
    assert result is False


def test_is_possibly_alive_no_birth_date():
    """Test is_possibly_alive when no birth date."""
    result = is_possibly_alive(None, None)
    assert result is False


def test_is_possibly_alive_invalid_birth_date():
    """Test is_possibly_alive with invalid birth date."""
    result = is_possibly_alive("invalid", None)
    assert result is False


def test_is_possibly_alive_old_person():
    """Test is_possibly_alive with person over 120 years old."""
    result = is_possibly_alive("01/01/1900", None)
    assert result is False


def test_is_possibly_alive_young_person():
    """Test is_possibly_alive with recent birth."""
    current_year = datetime.now().year
    recent_birth = f"01/01/{current_year - 30}"
    result = is_possibly_alive(recent_birth, None)
    assert result is True


def test_is_possibly_alive_exactly_120():
    """Test is_possibly_alive with person exactly 120 years old."""
    current_year = datetime.now().year
    birth = f"01/01/{current_year - 120}"
    result = is_possibly_alive(birth, None)
    assert result is True


def test_is_possibly_alive_121_years():
    """Test is_possibly_alive with person 121 years old."""
    current_year = datetime.now().year
    birth = f"01/01/{current_year - 121}"
    result = is_possibly_alive(birth, None)
    assert result is False
