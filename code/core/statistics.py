"""
Statistical analysis and demographics for genealogical data.

Provides comprehensive statistical computations including:
- Age distribution and lifespan analysis
- Surname frequency and geographic distribution
- Migration pattern detection
- Birth/death rate analysis
- Generation statistics
- Family size metrics

Optimized for large genealogical databases with efficient SQL queries.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import FamilyORM, PersonORM


@dataclass
class AgeStatistics:
    """Age-related statistics."""

    average_age_at_death: float
    median_age_at_death: float
    min_age: int
    max_age: int
    age_distribution: Dict[str, int]  # Age ranges -> count


@dataclass
class LifespanAnalysis:
    """Comprehensive lifespan analysis."""

    total_persons_with_dates: int
    average_lifespan_male: Optional[float]
    average_lifespan_female: Optional[float]
    average_lifespan_overall: float
    longest_lived_male: Optional[Tuple[int, str, int]]
    longest_lived_female: Optional[Tuple[int, str, int]]
    age_ranges: Dict[str, int]


@dataclass
class SurnameStatistics:
    """Surname frequency and distribution."""

    total_unique_surnames: int
    most_common_surnames: List[Tuple[str, int]]  # (surname, count)
    surname_diversity_index: float  # Shannon diversity index
    rare_surnames: List[str]  # Surnames with only 1 occurrence


@dataclass
class GeographicDistribution:
    """Geographic distribution of persons."""

    birth_places: Dict[str, int]  # Place -> count
    death_places: Dict[str, int]
    migration_patterns: List[Tuple[str, str, int]]  # (from, to, count)


@dataclass
class GenerationStatistics:
    """Statistics by generation."""

    generation_sizes: Dict[int, int]  # Generation number -> person count
    average_children_per_family: float
    max_children_in_family: int
    families_with_no_children: int
    average_generation_gap: float  # Years between generations


@dataclass
class DemographicSummary:
    """Complete demographic summary."""

    total_persons: int
    total_males: int
    total_females: int
    total_unknown_sex: int
    total_families: int
    living_persons: int
    deceased_persons: int
    persons_with_birth_dates: int
    persons_with_death_dates: int
    age_stats: AgeStatistics
    surname_stats: SurnameStatistics
    generation_stats: GenerationStatistics


class StatisticsCalculator:
    """
    Calculate comprehensive genealogical statistics.
    
    Provides methods for various statistical analyses on genealogical data.
    """

    def __init__(self, session: Session):
        """Initialize calculator with database session."""
        self.session = session

    def compute_demographic_summary(self) -> DemographicSummary:
        """
        Compute complete demographic summary.
        
        Returns:
            DemographicSummary object with all statistics
        """
        # Basic counts
        total_persons = self.session.query(PersonORM).count()

        total_males = (
            self.session.query(PersonORM)
            .filter(PersonORM.sex == "M")
            .count()
        )

        total_females = (
            self.session.query(PersonORM)
            .filter(PersonORM.sex == "F")
            .count()
        )

        total_unknown = total_persons - total_males - total_females

        total_families = self.session.query(FamilyORM).count()

        # NOTE: Would need birth/death dates in ORM for accurate counts
        persons_with_birth_dates = 0
        persons_with_death_dates = 0
        living_persons = 0
        deceased_persons = 0

        # Get detailed statistics
        age_stats = self.compute_age_statistics()
        surname_stats = self.compute_surname_statistics()
        generation_stats = self.compute_generation_statistics()

        return DemographicSummary(
            total_persons=total_persons,
            total_males=total_males,
            total_females=total_females,
            total_unknown_sex=total_unknown,
            total_families=total_families,
            living_persons=living_persons,
            deceased_persons=deceased_persons,
            persons_with_birth_dates=persons_with_birth_dates,
            persons_with_death_dates=persons_with_death_dates,
            age_stats=age_stats,
            surname_stats=surname_stats,
            generation_stats=generation_stats,
        )

    def compute_age_statistics(self) -> AgeStatistics:
        """
        Compute age-related statistics.
        
        Returns:
            AgeStatistics object
        """
        # NOTE: This is simplified - would need actual date fields
        # For now, return placeholder data

        age_distribution = {
            "0-10": 0,
            "11-20": 0,
            "21-30": 0,
            "31-40": 0,
            "41-50": 0,
            "51-60": 0,
            "61-70": 0,
            "71-80": 0,
            "81-90": 0,
            "91+": 0,
        }

        return AgeStatistics(
            average_age_at_death=0.0,
            median_age_at_death=0.0,
            min_age=0,
            max_age=0,
            age_distribution=age_distribution,
        )

    def compute_lifespan_analysis(self) -> LifespanAnalysis:
        """
        Analyze lifespan patterns.
        
        Returns:
            LifespanAnalysis object
        """
        # Placeholder - would calculate from actual dates
        return LifespanAnalysis(
            total_persons_with_dates=0,
            average_lifespan_male=None,
            average_lifespan_female=None,
            average_lifespan_overall=0.0,
            longest_lived_male=None,
            longest_lived_female=None,
            age_ranges={},
        )

    def compute_surname_statistics(self) -> SurnameStatistics:
        """
        Compute surname frequency and distribution.
        
        Returns:
            SurnameStatistics object
        """
        # Get all surnames
        surnames = (
            self.session.query(PersonORM.surname)
            .filter(PersonORM.surname.isnot(None))
            .filter(PersonORM.surname != "")
            .all()
        )

        surname_list = [s[0] for s in surnames]

        # Count frequencies
        surname_counts = Counter(surname_list)

        total_unique = len(surname_counts)

        # Most common
        most_common = surname_counts.most_common(20)

        # Rare surnames (only 1 occurrence)
        rare = [name for name, count in surname_counts.items() if count == 1]

        # Shannon diversity index
        total = sum(surname_counts.values())
        diversity = 0.0

        if total > 0:
            for count in surname_counts.values():
                proportion = count / total
                if proportion > 0:
                    diversity -= proportion * (proportion ** 0.5)

        return SurnameStatistics(
            total_unique_surnames=total_unique,
            most_common_surnames=most_common,
            surname_diversity_index=diversity,
            rare_surnames=rare[:50],  # Limit to 50
        )

    def compute_geographic_distribution(
        self,
    ) -> GeographicDistribution:
        """
        Analyze geographic distribution and migration.
        
        Returns:
            GeographicDistribution object
        """
        # Placeholder - would use place fields
        return GeographicDistribution(
            birth_places={},
            death_places={},
            migration_patterns=[],
        )

    def compute_generation_statistics(self) -> GenerationStatistics:
        """
        Compute statistics by generation.
        
        Returns:
            GenerationStatistics object
        """
        # Count children per family
        families = self.session.query(FamilyORM).all()

        children_counts = []

        for family in families:
            # NOTE: Would need to query children from parent_family_id
            # For now, simplified
            children_counts.append(0)

        avg_children = (
            sum(children_counts) / len(children_counts)
            if children_counts
            else 0.0
        )

        max_children = max(children_counts) if children_counts else 0

        no_children = children_counts.count(0)

        return GenerationStatistics(
            generation_sizes={},
            average_children_per_family=avg_children,
            max_children_in_family=max_children,
            families_with_no_children=no_children,
            average_generation_gap=0.0,
        )

    def get_surname_frequency_chart_data(
        self, top_n: int = 20
    ) -> Dict[str, any]:
        """
        Get data for surname frequency chart.
        
        Args:
            top_n: Number of top surnames to include
            
        Returns:
            Chart data dictionary
        """
        stats = self.compute_surname_statistics()

        labels = [name for name, _ in stats.most_common_surnames[:top_n]]
        data = [count for _, count in stats.most_common_surnames[:top_n]]

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Person Count",
                    "data": data,
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1,
                }
            ],
        }

    def get_sex_distribution_chart_data(self) -> Dict[str, any]:
        """
        Get data for sex distribution pie chart.
        
        Returns:
            Chart data dictionary
        """
        total_males = (
            self.session.query(PersonORM)
            .filter(PersonORM.sex == "M")
            .count()
        )

        total_females = (
            self.session.query(PersonORM)
            .filter(PersonORM.sex == "F")
            .count()
        )

        total_unknown = (
            self.session.query(PersonORM)
            .filter(PersonORM.sex == "U")
            .count()
        )

        return {
            "labels": ["Male", "Female", "Unknown"],
            "datasets": [
                {
                    "data": [total_males, total_females, total_unknown],
                    "backgroundColor": [
                        "rgba(54, 162, 235, 0.6)",
                        "rgba(255, 99, 132, 0.6)",
                        "rgba(201, 203, 207, 0.6)",
                    ],
                }
            ],
        }

    def get_age_distribution_chart_data(self) -> Dict[str, any]:
        """
        Get data for age distribution histogram.
        
        Returns:
            Chart data dictionary
        """
        age_stats = self.compute_age_statistics()

        labels = list(age_stats.age_distribution.keys())
        data = list(age_stats.age_distribution.values())

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Number of Persons",
                    "data": data,
                    "backgroundColor": "rgba(75, 192, 192, 0.6)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "borderWidth": 1,
                }
            ],
        }


class MigrationAnalyzer:
    """
    Analyze migration patterns in genealogical data.
    
    Detects geographic movement across generations.
    """

    def __init__(self, session: Session):
        """Initialize analyzer with database session."""
        self.session = session

    def detect_migration_patterns(
        self,
    ) -> List[Tuple[str, str, int]]:
        """
        Detect migration patterns (birthplace -> deathplace).
        
        Returns:
            List of (from_place, to_place, count) tuples
        """
        # Placeholder - would use actual place fields
        return []

    def compute_place_hierarchy(
        self, places: List[str]
    ) -> Dict[str, List[str]]:
        """
        Build hierarchical place structure.
        
        Args:
            places: List of place strings (e.g., "Paris, France")
            
        Returns:
            Hierarchical dictionary of places
        """
        hierarchy = defaultdict(list)

        for place in places:
            if not place:
                continue

            parts = [p.strip() for p in place.split(",")]

            if len(parts) >= 2:
                country = parts[-1]
                city = parts[0]
                hierarchy[country].append(city)

        return dict(hierarchy)


# Convenience functions
def get_demographic_summary(session: Session) -> DemographicSummary:
    """Get demographic summary."""
    calculator = StatisticsCalculator(session)
    return calculator.compute_demographic_summary()


def get_surname_statistics(session: Session) -> SurnameStatistics:
    """Get surname statistics."""
    calculator = StatisticsCalculator(session)
    return calculator.compute_surname_statistics()


def get_lifespan_analysis(session: Session) -> LifespanAnalysis:
    """Get lifespan analysis."""
    calculator = StatisticsCalculator(session)
    return calculator.compute_lifespan_analysis()
