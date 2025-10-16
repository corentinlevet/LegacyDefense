"""
Comprehensive event management system for genealogical data.

Supports all major genealogical event types:
- Birth, Death, Burial, Baptism
- Marriage, Divorce, Engagement
- Census, Military Service
- Immigration, Emigration
- Custom events

Features:
- French Revolutionary Calendar support
- Event validation and normalization
- Timeline generation
- Event templates
- Source citations
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from .models import Event, EventType


class FrenchRevolutionaryCalendar:
    """
    French Revolutionary Calendar converter.
    
    Converts between Gregorian and French Revolutionary calendars.
    Used from 1793-1805 in France.
    """

    # Month names in French
    MONTHS = [
        "Vendémiaire",
        "Brumaire",
        "Frimaire",
        "Nivôse",
        "Pluviôse",
        "Ventôse",
        "Germinal",
        "Floréal",
        "Prairial",
        "Messidor",
        "Thermidor",
        "Fructidor",
        "Jours Complémentaires",
    ]

    # Start date of Revolutionary calendar
    EPOCH = date(1792, 9, 22)

    @staticmethod
    def gregorian_to_revolutionary(greg_date: date) -> str:
        """
        Convert Gregorian date to Revolutionary calendar.
        
        Args:
            greg_date: Gregorian date
            
        Returns:
            Revolutionary date string (e.g., "5 Thermidor An III")
        """
        if greg_date < FrenchRevolutionaryCalendar.EPOCH:
            return "Before Revolutionary Calendar"

        # Calculate days since epoch
        delta = (greg_date - FrenchRevolutionaryCalendar.EPOCH).days

        # Calculate year (An I, An II, etc.)
        year = delta // 365 + 1

        # Calculate day of year
        day_of_year = delta % 365

        # Calculate month and day
        if day_of_year >= 360:
            # Complementary days (5 or 6 days at end of year)
            month_name = "Jours Complémentaires"
            day = day_of_year - 359
        else:
            month = day_of_year // 30
            day = (day_of_year % 30) + 1
            month_name = FrenchRevolutionaryCalendar.MONTHS[month]

        return f"{day} {month_name} An {year}"

    @staticmethod
    def parse_revolutionary_date(rev_date: str) -> Optional[date]:
        """
        Parse Revolutionary date string to Gregorian date.
        
        Args:
            rev_date: Revolutionary date (e.g., "5 Thermidor An III")
            
        Returns:
            Gregorian date or None if invalid
        """
        # Simplified parser - would need more robust implementation
        parts = rev_date.split()

        if len(parts) < 4 or parts[2].lower() != "an":
            return None

        try:
            day = int(parts[0])
            month_name = parts[1]
            year = int(parts[3])

            # Find month index
            if month_name not in FrenchRevolutionaryCalendar.MONTHS:
                return None

            month_idx = FrenchRevolutionaryCalendar.MONTHS.index(month_name)

            # Calculate days from epoch
            days_from_epoch = (year - 1) * 365 + month_idx * 30 + (day - 1)

            # Add to epoch
            import datetime as dt

            result_date = (
                FrenchRevolutionaryCalendar.EPOCH
                + dt.timedelta(days=days_from_epoch)
            )

            return result_date

        except (ValueError, IndexError):
            return None


@dataclass
class DatePrecision(Enum):
    """Precision level of a date."""

    EXACT = "exact"  # Exact date known
    ABOUT = "about"  # Approximate date
    BEFORE = "before"  # Before this date
    AFTER = "after"  # After this date
    BETWEEN = "between"  # Between two dates
    YEAR_ONLY = "year"  # Only year known
    MONTH_YEAR = "month_year"  # Month and year known


@dataclass
class GenealogicalDate:
    """
    Flexible date representation for genealogical data.
    
    Supports various precision levels and calendar systems.
    """

    precision: DatePrecision
    date1: Optional[date] = None
    date2: Optional[date] = None  # For "between" dates
    year: Optional[int] = None
    month: Optional[int] = None
    calendar: str = "gregorian"  # "gregorian" or "revolutionary"
    original_text: Optional[str] = None

    def to_display_string(self) -> str:
        """Convert to human-readable string."""
        if self.precision == DatePrecision.EXACT and self.date1:
            if self.calendar == "revolutionary":
                return FrenchRevolutionaryCalendar.gregorian_to_revolutionary(
                    self.date1
                )
            return self.date1.strftime("%d %B %Y")

        elif self.precision == DatePrecision.ABOUT and self.year:
            return f"About {self.year}"

        elif self.precision == DatePrecision.BEFORE and self.year:
            return f"Before {self.year}"

        elif self.precision == DatePrecision.AFTER and self.year:
            return f"After {self.year}"

        elif self.precision == DatePrecision.BETWEEN and self.date1 and self.date2:
            return f"Between {self.date1.year} and {self.date2.year}"

        elif self.precision == DatePrecision.YEAR_ONLY and self.year:
            return str(self.year)

        elif self.precision == DatePrecision.MONTH_YEAR and self.month and self.year:
            month_names = [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]
            return f"{month_names[self.month - 1]} {self.year}"

        return self.original_text or "Unknown date"

    @staticmethod
    def parse(date_string: str) -> "GenealogicalDate":
        """
        Parse date string to GenealogicalDate.
        
        Args:
            date_string: Date string (various formats)
            
        Returns:
            GenealogicalDate object
        """
        if not date_string:
            return GenealogicalDate(
                precision=DatePrecision.EXACT, original_text="Unknown"
            )

        date_string = date_string.strip().lower()

        # Check for "about" prefix
        if date_string.startswith("about") or date_string.startswith("abt"):
            year_str = date_string.split()[-1]
            try:
                year = int(year_str)
                return GenealogicalDate(
                    precision=DatePrecision.ABOUT,
                    year=year,
                    original_text=date_string,
                )
            except ValueError:
                pass

        # Check for "before"
        if date_string.startswith("before") or date_string.startswith("bef"):
            year_str = date_string.split()[-1]
            try:
                year = int(year_str)
                return GenealogicalDate(
                    precision=DatePrecision.BEFORE,
                    year=year,
                    original_text=date_string,
                )
            except ValueError:
                pass

        # Check for "after"
        if date_string.startswith("after") or date_string.startswith("aft"):
            year_str = date_string.split()[-1]
            try:
                year = int(year_str)
                return GenealogicalDate(
                    precision=DatePrecision.AFTER,
                    year=year,
                    original_text=date_string,
                )
            except ValueError:
                pass

        # Check for "between"
        if "between" in date_string and "and" in date_string:
            parts = date_string.split("and")
            if len(parts) == 2:
                try:
                    year1 = int(parts[0].split()[-1])
                    year2 = int(parts[1].strip())
                    return GenealogicalDate(
                        precision=DatePrecision.BETWEEN,
                        date1=date(year1, 1, 1),
                        date2=date(year2, 12, 31),
                        year=year1,
                        original_text=date_string,
                    )
                except ValueError:
                    pass

        # Try to parse as exact date
        try:
            # Try ISO format
            parsed_date = datetime.strptime(date_string, "%Y-%m-%d").date()
            return GenealogicalDate(
                precision=DatePrecision.EXACT,
                date1=parsed_date,
                year=parsed_date.year,
                month=parsed_date.month,
                original_text=date_string,
            )
        except ValueError:
            pass

        # Try year only
        try:
            year = int(date_string)
            if 1000 <= year <= 2100:
                return GenealogicalDate(
                    precision=DatePrecision.YEAR_ONLY,
                    year=year,
                    original_text=date_string,
                )
        except ValueError:
            pass

        # Fallback
        return GenealogicalDate(
            precision=DatePrecision.EXACT, original_text=date_string
        )


class EventValidator:
    """Validate and normalize genealogical events."""

    @staticmethod
    def validate_birth(event: Event) -> List[str]:
        """
        Validate birth event.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if event.event_type != EventType.BIRTH:
            errors.append("Event type must be BIRTH")

        # Birth should have a date
        if not event.date:
            errors.append("Birth event should have a date")

        return errors

    @staticmethod
    def validate_death(event: Event, birth_event: Optional[Event]) -> List[str]:
        """
        Validate death event.
        
        Args:
            event: Death event
            birth_event: Birth event (if available)
            
        Returns:
            List of validation errors
        """
        errors = []

        if event.event_type != EventType.DEATH:
            errors.append("Event type must be DEATH")

        # Death should have a date
        if not event.date:
            errors.append("Death event should have a date")

        # Death date should be after birth date
        if birth_event and event.date and birth_event.date:
            # NOTE: Would need to parse dates for comparison
            pass

        return errors

    @staticmethod
    def validate_marriage(event: Event) -> List[str]:
        """Validate marriage event."""
        errors = []

        if event.event_type != EventType.MARRIAGE:
            errors.append("Event type must be MARRIAGE")

        return errors


class TimelineGenerator:
    """Generate timelines from events."""

    @staticmethod
    def create_person_timeline(
        events: List[Event],
    ) -> List[dict]:
        """
        Create timeline for a person.
        
        Args:
            events: List of events
            
        Returns:
            Timeline data (sorted by date)
        """
        timeline = []

        for event in events:
            timeline_item = {
                "type": event.event_type.value,
                "date": event.date,
                "place": event.place,
                "note": event.note,
                "icon": TimelineGenerator._get_event_icon(event.event_type),
                "color": TimelineGenerator._get_event_color(event.event_type),
            }

            timeline.append(timeline_item)

        # Sort by date (handle None dates)
        timeline.sort(key=lambda x: x["date"] or "9999-12-31")

        return timeline

    @staticmethod
    def _get_event_icon(event_type: EventType) -> str:
        """Get Font Awesome icon for event type."""
        icons = {
            EventType.BIRTH: "fa-birthday-cake",
            EventType.DEATH: "fa-cross",
            EventType.BURIAL: "fa-monument",
            EventType.BAPTISM: "fa-water",
            EventType.MARRIAGE: "fa-ring",
            EventType.DIVORCE: "fa-heartbroken",
            EventType.CENSUS: "fa-users",
            EventType.RESIDENCE: "fa-home",
            EventType.IMMIGRATION: "fa-plane-arrival",
            EventType.EMIGRATION: "fa-plane-departure",
            EventType.MILITARY_SERVICE: "fa-shield-alt",
            EventType.OCCUPATION: "fa-briefcase",
            EventType.OTHER: "fa-info-circle",
        }

        return icons.get(event_type, "fa-calendar")

    @staticmethod
    def _get_event_color(event_type: EventType) -> str:
        """Get color for event type."""
        colors = {
            EventType.BIRTH: "#27ae60",
            EventType.DEATH: "#e74c3c",
            EventType.BURIAL: "#95a5a6",
            EventType.BAPTISM: "#3498db",
            EventType.MARRIAGE: "#e91e63",
            EventType.DIVORCE: "#ff5722",
            EventType.CENSUS: "#9c27b0",
            EventType.RESIDENCE: "#00bcd4",
            EventType.IMMIGRATION: "#009688",
            EventType.EMIGRATION: "#ff9800",
            EventType.MILITARY_SERVICE: "#795548",
            EventType.OCCUPATION: "#607d8b",
            EventType.OTHER: "#9e9e9e",
        }

        return colors.get(event_type, "#000000")


# Event templates for common event types
EVENT_TEMPLATES = {
    "birth": Event(
        event_type=EventType.BIRTH,
        date=None,
        place="",
        note="Birth of person",
    ),
    "death": Event(
        event_type=EventType.DEATH, date=None, place="", note="Death of person"
    ),
    "marriage": Event(
        event_type=EventType.MARRIAGE,
        date=None,
        place="",
        note="Marriage ceremony",
    ),
    "baptism": Event(
        event_type=EventType.BAPTISM,
        date=None,
        place="",
        note="Baptism ceremony",
    ),
    "burial": Event(
        event_type=EventType.BURIAL, date=None, place="", note="Burial"
    ),
}


def create_event_from_template(template_name: str) -> Event:
    """
    Create event from template.
    
    Args:
        template_name: Name of template
        
    Returns:
        Event object
    """
    template = EVENT_TEMPLATES.get(template_name)

    if not template:
        return Event(
            event_type=EventType.OTHER, date=None, place="", note=""
        )

    return Event(
        event_type=template.event_type,
        date=template.date,
        place=template.place,
        note=template.note,
    )
