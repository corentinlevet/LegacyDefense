"""
Shared test fixtures and configuration for the GeneWeb Python test suite.

This module provides reusable fixtures across all test modules,
following pytest best practices for DRY test infrastructure.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Database Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db_session():
    """Provide a mocked SQLAlchemy database session."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    session.commit.return_value = None
    session.close.return_value = None
    session.add.return_value = None
    session.flush.return_value = None
    return session


@pytest.fixture
def mock_session_local(mock_db_session):
    """Patch SessionLocal to return the mocked session."""
    with patch(
        "src.geneweb.application.services.SessionLocal",
        return_value=mock_db_session,
    ) as mock_sl:
        yield mock_sl


# ---------------------------------------------------------------------------
# Model Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_person():
    """Create a sample Person mock for testing."""
    person = MagicMock()
    person.id = 1
    person.genealogy_id = 1
    person.first_name = "Jean"
    person.surname = "Dupont"
    person.sex = "M"
    person.birth_date = "15 JAN 1980"
    person.birth_place = "Paris"
    person.death_date = None
    person.death_place = None
    person.baptism_date = None
    person.baptism_place = None
    person.burial_date = None
    person.burial_place = None
    person.occupation = "Artisan"
    person.notes = "Test person"
    return person


@pytest.fixture
def sample_family():
    """Create a sample Family mock for testing."""
    family = MagicMock()
    family.id = 1
    family.genealogy_id = 1
    family.father_id = 1
    family.mother_id = 2
    family.marriage_date = "15 JUN 2005"
    family.marriage_place = "Lyon"
    family.divorce_date = None
    family.children = []
    return family


@pytest.fixture
def sample_genealogy():
    """Create a sample Genealogy mock for testing."""
    genealogy = MagicMock()
    genealogy.id = 1
    genealogy.name = "test_genealogy"
    return genealogy


# ---------------------------------------------------------------------------
# Service Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_genealogy_repo():
    """Provide a mocked SQLGenealogyRepository."""
    repo = MagicMock()
    repo.get_by_name = MagicMock(return_value=None)
    repo.count_persons = MagicMock(return_value=0)
    repo.get_first_names = MagicMock(return_value=[])
    repo.get_last_names = MagicMock(return_value=[])
    repo.get_places_from_births = MagicMock(return_value=[])
    repo.get_places_from_deaths = MagicMock(return_value=[])
    repo.get_occupations = MagicMock(return_value=[])
    repo.get_sources = MagicMock(return_value=[])
    return repo


# ---------------------------------------------------------------------------
# Date Test Data
# ---------------------------------------------------------------------------


@pytest.fixture
def gedcom_date_samples():
    """Provide GEDCOM date format samples for testing."""
    return {
        "full": "15 JAN 1980",
        "month_year": "JAN 1980",
        "year_only": "1980",
        "about": "ABT 1980",
        "before": "BEF 1980",
        "after": "AFT 1980",
        "between": "BET 1970 AND 1980",
        "french_format": "15/01/1980",
        "iso_format": "1980-01-15",
    }
