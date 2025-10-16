"""
Protocol interfaces for GeneWeb Python implementation.

This module defines abstract interfaces (using Python's Protocol) to enable
dependency inversion and interface segregation, following SOLID principles.
"""

from typing import Any, Dict, List, Optional, Protocol, Set

from .models import Database, Event, Family, Person, Sex


class PersonRepository(Protocol):
    """Abstract repository for Person entity operations.

    This protocol defines the interface for person data access,
    allowing different implementations (SQL, NoSQL, in-memory, etc.)
    without changing client code.
    """

    def find_by_id(self, person_id: int) -> Optional[Person]:
        """
        Retrieve a person by their unique identifier.

        Args:
            person_id: Unique identifier of the person

        Returns:
            Person object if found, None otherwise
        """
        ...

    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Person]:
        """
        Retrieve all persons with optional pagination.

        Args:
            limit: Maximum number of persons to return
            offset: Number of persons to skip

        Returns:
            List of Person objects
        """
        ...

    def find_by_name(
        self, first_name: Optional[str] = None, surname: Optional[str] = None
    ) -> List[Person]:
        """
        Find persons by name (partial match supported).

        Args:
            first_name: First name to search for (optional)
            surname: Surname to search for (optional)

        Returns:
            List of matching Person objects
        """
        ...

    def save(self, person: Person) -> int:
        """
        Save a person (create or update).

        Args:
            person: Person object to save

        Returns:
            ID of the saved person
        """
        ...

    def delete(self, person_id: int) -> bool:
        """
        Delete a person by ID.

        Args:
            person_id: ID of person to delete

        Returns:
            True if deleted, False if not found
        """
        ...


class FamilyRepository(Protocol):
    """Abstract repository for Family entity operations."""

    def find_by_id(self, family_id: int) -> Optional[Family]:
        """Retrieve a family by ID."""
        ...

    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Family]:
        """Retrieve all families with pagination."""
        ...

    def find_by_parent(self, parent_id: int) -> List[Family]:
        """Find all families where person is a parent."""
        ...

    def find_by_child(self, child_id: int) -> Optional[Family]:
        """Find family where person is a child."""
        ...

    def save(self, family: Family) -> int:
        """Save a family (create or update)."""
        ...

    def delete(self, family_id: int) -> bool:
        """Delete a family by ID."""
        ...


class EventRepository(Protocol):
    """Abstract repository for Event entity operations."""

    def find_by_id(self, event_id: int) -> Optional[Event]:
        """Retrieve an event by ID."""
        ...

    def find_by_person(self, person_id: int) -> List[Event]:
        """Find all events for a person."""
        ...

    def find_by_family(self, family_id: int) -> List[Event]:
        """Find all events for a family."""
        ...

    def save(self, event: Event) -> int:
        """Save an event (create or update)."""
        ...

    def delete(self, event_id: int) -> bool:
        """Delete an event by ID."""
        ...


class AncestryQuery(Protocol):
    """Query interface for ancestry operations.

    Follows Interface Segregation Principle - clients that only need
    to query ancestry don't need to depend on modification operations.
    """

    def get_ancestors(
        self, person_id: int, max_generations: Optional[int] = None
    ) -> Set[int]:
        """
        Get all ancestors of a person.

        Args:
            person_id: ID of the person
            max_generations: Maximum number of generations to traverse

        Returns:
            Set of ancestor person IDs
        """
        ...

    def get_descendants(
        self, person_id: int, max_generations: Optional[int] = None
    ) -> Set[int]:
        """
        Get all descendants of a person.

        Args:
            person_id: ID of the person
            max_generations: Maximum number of generations to traverse

        Returns:
            Set of descendant person IDs
        """
        ...

    def find_common_ancestors(self, person1_id: int, person2_id: int) -> Set[int]:
        """
        Find common ancestors between two persons.

        Args:
            person1_id: ID of first person
            person2_id: ID of second person

        Returns:
            Set of common ancestor person IDs
        """
        ...


class ConsanguinityCalculator(Protocol):
    """Calculate consanguinity (blood relationship) coefficients.

    Following Open/Closed Principle - new calculation algorithms can be
    added by implementing this protocol without modifying existing code.
    """

    def calculate(self, person_id: int) -> float:
        """
        Calculate Wright's coefficient of consanguinity for a person.

        The coefficient represents the probability that two alleles at a
        random locus in an individual are identical by descent.

        Args:
            person_id: ID of the person

        Returns:
            Consanguinity coefficient (0.0 to 1.0)
        """
        ...

    def calculate_for_pair(self, person1_id: int, person2_id: int) -> float:
        """
        Calculate consanguinity coefficient between two persons.

        Args:
            person1_id: ID of first person
            person2_id: ID of second person

        Returns:
            Consanguinity coefficient between the two persons
        """
        ...


class RelationshipDetector(Protocol):
    """Detect and describe relationships between persons.

    Examples: "father", "grandmother", "first cousin", "uncle", etc.
    """

    def detect_relationship(self, person1_id: int, person2_id: int) -> Optional[str]:
        """
        Detect the relationship between two persons.

        Args:
            person1_id: ID of first person
            person2_id: ID of second person

        Returns:
            Human-readable relationship description, or None if no relation
        """
        ...

    def is_ancestor(self, ancestor_id: int, descendant_id: int) -> bool:
        """Check if person1 is an ancestor of person2."""
        ...

    def is_descendant(self, descendant_id: int, ancestor_id: int) -> bool:
        """Check if person1 is a descendant of person2."""
        ...


class GedcomParser(Protocol):
    """Parse GEDCOM genealogy files.

    Following Open/Closed Principle - can have multiple parsers for
    different GEDCOM versions or dialects.
    """

    def parse(self, file_path: str) -> Database:
        """
        Parse a GEDCOM file into a Database object.

        Args:
            file_path: Path to GEDCOM file

        Returns:
            Database object containing parsed data

        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file doesn't exist
        """
        ...

    def supports_version(self, version: str) -> bool:
        """Check if this parser supports a specific GEDCOM version."""
        ...


class GedcomExporter(Protocol):
    """Export database to GEDCOM format."""

    def export(self, database: Database, file_path: str) -> None:
        """
        Export a Database to GEDCOM file.

        Args:
            database: Database object to export
            file_path: Path where GEDCOM file should be written

        Raises:
            IOError: If file cannot be written
        """
        ...

    def get_version(self) -> str:
        """Get the GEDCOM version this exporter produces."""
        ...


class Exporter(Protocol):
    """Generic data export interface.

    Following Open/Closed Principle - new export formats can be added
    by implementing this protocol.
    """

    def export(self, database: Database) -> bytes:
        """
        Export database to a specific format.

        Args:
            database: Database object to export

        Returns:
            Exported data as bytes
        """
        ...

    def get_content_type(self) -> str:
        """Get MIME type of exported content."""
        ...

    def get_file_extension(self) -> str:
        """Get file extension for exported files."""
        ...


class TemplateRenderer(Protocol):
    """Render templates with data.

    Abstract interface for template engines (Jinja2, Mako, etc.).
    """

    def render(self, template_name: str, **context: Any) -> str:
        """
        Render a template with given context.

        Args:
            template_name: Name/path of template
            **context: Variables to pass to template

        Returns:
            Rendered template as string
        """
        ...

    def render_string(self, template_string: str, **context: Any) -> str:
        """
        Render a template from string.

        Args:
            template_string: Template content as string
            **context: Variables to pass to template

        Returns:
            Rendered template as string
        """
        ...


class CacheProvider(Protocol):
    """Generic cache interface.

    Can be implemented with Redis, Memcached, in-memory dict, etc.
    """

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache by key."""
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = no expiration)
        """
        ...

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        ...

    def clear(self) -> None:
        """Clear all cache entries."""
        ...


class Logger(Protocol):
    """Logging interface.

    Abstract interface for different logging implementations.
    """

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        ...

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        ...


class AuthenticationService(Protocol):
    """User authentication interface."""

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate user and return token.

        Args:
            username: User's username
            password: User's password

        Returns:
            Authentication token if successful, None otherwise
        """
        ...

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate authentication token.

        Args:
            token: Token to validate

        Returns:
            User information if valid, None otherwise
        """
        ...


class AuthorizationService(Protocol):
    """User authorization interface."""

    def has_permission(self, user_id: int, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_id: ID of user
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        ...

    def get_user_permissions(self, user_id: int) -> Set[str]:
        """Get all permissions for a user."""
        ...


class PrivacyFilter(Protocol):
    """Filter data based on privacy rules.

    Implements privacy protection for living individuals (GDPR compliance).
    """

    def filter_person(self, person: Person, viewer_id: Optional[int] = None) -> Person:
        """
        Filter person data based on privacy rules.

        Args:
            person: Person to filter
            viewer_id: ID of user viewing the data (None = anonymous)

        Returns:
            Filtered Person object with private data redacted if needed
        """
        ...

    def is_living(self, person: Person) -> bool:
        """Determine if a person is considered living."""
        ...

    def can_view_full_data(
        self, person: Person, viewer_id: Optional[int] = None
    ) -> bool:
        """Check if viewer can see full data for a person."""
        ...
