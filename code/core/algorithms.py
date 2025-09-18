"""
Genealogical algorithms for GeneWeb Python implementation.

This module contains algorithms for consanguinity calculation, relationship
analysis, and other genealogy-specific computations ported from the original
OCaml implementation.
"""
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import math

from .models import Person, Family, Sex
from .database import PersonORM, FamilyORM, DatabaseManager


class RelationType(Enum):
    """Types of family relationships."""
    SELF = "self"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    HALF_SIBLING = "half_sibling"
    GRANDPARENT = "grandparent"
    GRANDCHILD = "grandchild"
    UNCLE_AUNT = "uncle_aunt"
    NEPHEW_NIECE = "nephew_niece"
    COUSIN = "cousin"
    COUSIN_ONCE_REMOVED = "cousin_once_removed"
    COUSIN_TWICE_REMOVED = "cousin_twice_removed"
    GREAT_GRANDPARENT = "great_grandparent"
    GREAT_GRANDCHILD = "great_grandchild"
    DISTANT_RELATIVE = "distant_relative"
    SPOUSE = "spouse"
    UNKNOWN = "unknown"


@dataclass
class FamilyLink:
    """Represents a single step in a family relationship path."""
    person_id: int
    relation_type: RelationType
    distance: int  # Generation distance
    is_paternal: bool  # True if through father's line, False if mother's line


@dataclass
class RelationshipPath:
    """Represents a complete path between two persons through common ancestors."""
    person1_id: int
    person2_id: int
    common_ancestor_id: int
    person1_distance: int  # Distance from person1 to common ancestor
    person2_distance: int  # Distance from person2 to common ancestor
    path_type: str  # 'paternal', 'maternal', 'mixed'
    person1_path: List[FamilyLink]  # Detailed path from person1 to ancestor
    person2_path: List[FamilyLink]  # Detailed path from person2 to ancestor
    relationship_name: str  # Human-readable relationship name


@dataclass
class RelationshipSummary:
    """Summary of relationship between two persons."""
    person1_id: int
    person2_id: int
    primary_relationship: RelationType
    relationship_description: str
    consanguinity: float
    paths: List[RelationshipPath]
    common_ancestors: List[int]
    closest_common_ancestor: Optional[int]


@dataclass
class ConsanguinityResult:
    """Result of consanguinity calculation."""
    person_id: int
    consanguinity: float
    relationship_paths: List[RelationshipPath]
    common_ancestors: Set[int]


class GenealogyAlgorithms:
    """Algorithms for genealogical computations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db_manager = db_manager
        self._ancestor_cache: Dict[int, Set[int]] = {}
        self._descendant_cache: Dict[int, Set[int]] = {}
        self._consanguinity_cache: Dict[int, float] = {}  # Cache pour consanguinité
        self._cache_hits = 0  # Compteur de hits de cache
        self._cache_misses = 0  # Compteur de misses de cache
    
    def clear_cache(self):
        """Clear internal caches."""
        self._ancestor_cache.clear()
        self._descendant_cache.clear()
        self._consanguinity_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_ancestors(self, session, person_id: int, max_generations: int = 50) -> Set[int]:
        """Get all ancestors of a person up to max_generations."""
        if person_id in self._ancestor_cache:
            return self._ancestor_cache[person_id]
        
        ancestors = set()
        queue = [(person_id, 0)]
        visited = set()
        
        while queue:
            current_id, generation = queue.pop(0)
            
            if generation >= max_generations or current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Get person's parent family
            person = session.query(PersonORM).filter(PersonORM.id == current_id).first()
            if not person or not person.parent_family:
                continue
            
            family = person.parent_family
            
            # Add parents as ancestors
            if family.father_id and family.father_id not in ancestors:
                ancestors.add(family.father_id)
                queue.append((family.father_id, generation + 1))
            
            if family.mother_id and family.mother_id not in ancestors:
                ancestors.add(family.mother_id)
                queue.append((family.mother_id, generation + 1))
        
        self._ancestor_cache[person_id] = ancestors
        return ancestors
    
    def get_descendants(self, session, person_id: int, max_generations: int = 50) -> Set[int]:
        """Get all descendants of a person up to max_generations."""
        if person_id in self._descendant_cache:
            return self._descendant_cache[person_id]
        
        descendants = set()
        queue = [(person_id, 0)]
        visited = set()
        
        while queue:
            current_id, generation = queue.pop(0)
            
            if generation >= max_generations or current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Get families where person is a parent
            families = session.query(FamilyORM).filter(
                (FamilyORM.father_id == current_id) | 
                (FamilyORM.mother_id == current_id)
            ).all()
            
            for family in families:
                # Get children
                children = session.query(PersonORM).filter(
                    PersonORM.parent_family_id == family.id
                ).all()
                
                for child in children:
                    if child.id not in descendants:
                        descendants.add(child.id)
                        queue.append((child.id, generation + 1))
        
        self._descendant_cache[person_id] = descendants
        return descendants
    
    def get_descendants_by_generation(self, session, person_id: int, max_generations: int = 50) -> List[List[PersonORM]]:
        """Get descendants organized by generation."""
        generations = []
        queue = [(person_id, 0)]
        visited = set()
        generation_dict = {}
        
        while queue:
            current_id, generation = queue.pop(0)
            
            if generation >= max_generations or current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Skip the root person (generation 0)
            if generation == 0:
                # Get families where person is a parent
                families = session.query(FamilyORM).filter(
                    (FamilyORM.father_id == current_id) | 
                    (FamilyORM.mother_id == current_id)
                ).all()
                
                for family in families:
                    # Get children
                    children = session.query(PersonORM).filter(
                        PersonORM.parent_family_id == family.id
                    ).all()
                    
                    for child in children:
                        if child.id not in visited:
                            queue.append((child.id, generation + 1))
                continue
            
            # Add person to the appropriate generation
            if generation not in generation_dict:
                generation_dict[generation] = []
            
            person = session.query(PersonORM).filter(PersonORM.id == current_id).first()
            if person:
                generation_dict[generation].append(person)
            
            # Get families where person is a parent
            families = session.query(FamilyORM).filter(
                (FamilyORM.father_id == current_id) | 
                (FamilyORM.mother_id == current_id)
            ).all()
            
            for family in families:
                # Get children
                children = session.query(PersonORM).filter(
                    PersonORM.parent_family_id == family.id
                ).all()
                
                for child in children:
                    if child.id not in visited:
                        queue.append((child.id, generation + 1))
        
        # Convert dict to ordered list of generations
        max_gen = max(generation_dict.keys()) if generation_dict else 0
        for gen in range(1, max_gen + 1):
            if gen in generation_dict:
                generations.append(generation_dict[gen])
            else:
                generations.append([])
        
        return generations
    
    def find_common_ancestors(self, session, person1_id: int, person2_id: int) -> Set[int]:
        """Find common ancestors between two persons."""
        ancestors1 = self.get_ancestors(session, person1_id)
        ancestors2 = self.get_ancestors(session, person2_id)
        return ancestors1.intersection(ancestors2)
    
    def calculate_relationship_distance(self, session, person1_id: int, person2_id: int) -> Optional[Tuple[int, int, int]]:
        """
        Calculate relationship distance between two persons.
        Returns (common_ancestor_id, distance1, distance2) or None if not related.
        """
        # First check for direct relationships (parent-child, siblings)
        
        # Check if person1 is parent of person2
        person2 = session.query(PersonORM).filter(PersonORM.id == person2_id).first()
        if person2 and person2.parent_family:
            if (person2.parent_family.father_id == person1_id or 
                person2.parent_family.mother_id == person1_id):
                # person1 is parent of person2: distance (person1=ancestor, 0, 1)
                return (person1_id, 0, 1)
        
        # Check if person2 is parent of person1
        person1 = session.query(PersonORM).filter(PersonORM.id == person1_id).first()
        if person1 and person1.parent_family:
            if (person1.parent_family.father_id == person2_id or 
                person1.parent_family.mother_id == person2_id):
                # person2 is parent of person1: distance (person2=ancestor, 1, 0)
                return (person2_id, 1, 0)
        
        # Check if they are siblings (same parents)
        if (person1 and person1.parent_family and 
            person2 and person2.parent_family and
            person1.parent_family.id == person2.parent_family.id):
            # They are siblings, find a common parent as "common ancestor"
            if person1.parent_family.father_id:
                return (person1.parent_family.father_id, 1, 1)
            elif person1.parent_family.mother_id:
                return (person1.parent_family.mother_id, 1, 1)
        
        # If no direct relationship, look for common ancestors
        common_ancestors = self.find_common_ancestors(session, person1_id, person2_id)
        
        if not common_ancestors:
            return None
        
        # Find the closest common ancestor (shortest total distance)
        min_distance = float('inf')
        best_ancestor = None
        best_distances = None
        
        for ancestor_id in common_ancestors:
            dist1 = self._distance_to_ancestor(session, person1_id, ancestor_id)
            dist2 = self._distance_to_ancestor(session, person2_id, ancestor_id)
            
            if dist1 is not None and dist2 is not None:
                total_distance = dist1 + dist2
                if total_distance < min_distance:
                    min_distance = total_distance
                    best_ancestor = ancestor_id
                    best_distances = (dist1, dist2)
        
        if best_ancestor is not None:
            return (best_ancestor, best_distances[0], best_distances[1])
        
        return None
    
    def _distance_to_ancestor(self, session, person_id: int, ancestor_id: int) -> Optional[int]:
        """Calculate distance from person to specific ancestor."""
        if person_id == ancestor_id:
            return 0
        
        queue = [(person_id, 0)]
        visited = set()
        
        while queue:
            current_id, distance = queue.pop(0)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id == ancestor_id:
                return distance
            
            # Get parents
            person = session.query(PersonORM).filter(PersonORM.id == current_id).first()
            if not person or not person.parent_family:
                continue
            
            family = person.parent_family
            
            if family.father_id and family.father_id not in visited:
                queue.append((family.father_id, distance + 1))
            
            if family.mother_id and family.mother_id not in visited:
                queue.append((family.mother_id, distance + 1))
        
        return None
    
    def calculate_consanguinity(self, session, person_id: int) -> ConsanguinityResult:
        """
        Calculate consanguinity coefficient for a person.
        
        Consanguinity is the probability that two alleles at a locus in an 
        individual are identical by descent.
        """
        person = session.query(PersonORM).filter(PersonORM.id == person_id).first()
        if not person or not person.parent_family:
            return ConsanguinityResult(
                person_id=person_id,
                consanguinity=0.0,
                relationship_paths=[],
                common_ancestors=set()
            )
        
        family = person.parent_family
        
        if not family.father_id or not family.mother_id:
            return ConsanguinityResult(
                person_id=person_id,
                consanguinity=0.0,
                relationship_paths=[],
                common_ancestors=set()
            )
        
        # Find common ancestors between parents
        common_ancestors = self.find_common_ancestors(session, family.father_id, family.mother_id)
        
        if not common_ancestors:
            return ConsanguinityResult(
                person_id=person_id,
                consanguinity=0.0,
                relationship_paths=[],
                common_ancestors=set()
            )
        
        # Calculate consanguinity coefficient
        total_consanguinity = 0.0
        relationship_paths = []
        
        for ancestor_id in common_ancestors:
            father_distance = self._distance_to_ancestor(session, family.father_id, ancestor_id)
            mother_distance = self._distance_to_ancestor(session, family.mother_id, ancestor_id)
            
            if father_distance is not None and mother_distance is not None:
                # Consanguinity contribution from this path
                # Formula: (1/2)^(n1 + n2 + 1) where n1, n2 are distances to common ancestor
                path_consanguinity = (0.5) ** (father_distance + mother_distance + 1)
                
                # Account for inbreeding of the common ancestor
                ancestor_consanguinity = self._get_person_consanguinity(session, ancestor_id)
                path_consanguinity *= (1 + ancestor_consanguinity)
                
                total_consanguinity += path_consanguinity
                
                relationship_paths.append(RelationshipPath(
                    person1_id=family.father_id,
                    person2_id=family.mother_id,
                    common_ancestor_id=ancestor_id,
                    person1_distance=father_distance,
                    person2_distance=mother_distance,
                    path_type='mixed',
                    person1_path=[],  # Chemins détaillés non nécessaires pour consanguinité
                    person2_path=[],
                    relationship_name=f"Ancêtre commun (distance {father_distance}+{mother_distance})"
                ))
        
        return ConsanguinityResult(
            person_id=person_id,
            consanguinity=total_consanguinity,
            relationship_paths=relationship_paths,
            common_ancestors=common_ancestors
        )
    
    def _get_person_consanguinity(self, session, person_id: int) -> float:
        """Get existing consanguinity value for a person."""
        person = session.query(PersonORM).filter(PersonORM.id == person_id).first()
        return person.consang if person else 0.0
    
    def compute_all_consanguinity(self, session, from_scratch: bool = False, verbosity: int = 1) -> Dict[int, float]:
        """
        Compute consanguinity for all persons in the database.
        Returns dict of person_id -> consanguinity_value.
        """
        results = {}
        
        # Get all persons
        persons = session.query(PersonORM).all()
        total_persons = len(persons)
        
        if verbosity > 0:
            print(f"Computing consanguinity for {total_persons} persons...")
        
        # Sort persons by generation (process ancestors before descendants)
        persons_by_generation = self._sort_by_generation(session, persons)
        
        processed = 0
        for generation, generation_persons in enumerate(persons_by_generation):
            if verbosity > 1:
                print(f"Processing generation {generation} ({len(generation_persons)} persons)...")
            
            for person in generation_persons:
                if from_scratch or person.consang == 0.0:
                    result = self.calculate_consanguinity(session, person.id)
                    person.consang = result.consanguinity
                    results[person.id] = result.consanguinity
                    processed += 1
                else:
                    results[person.id] = person.consang
                
                if verbosity > 1 and processed % 100 == 0:
                    print(f"  Processed {processed}/{total_persons} persons...")
        
        # Commit changes
        session.commit()
        
        if verbosity > 0:
            print(f"Computed consanguinity for {processed} persons")
        
        return results
    
    def _sort_by_generation(self, session, persons: List[PersonORM]) -> List[List[PersonORM]]:
        """Sort persons by generation (ancestors first)."""
        # Simple approach: group by maximum distance to any descendant
        generation_map = {}
        
        for person in persons:
            max_depth = self._max_descendant_depth(session, person.id)
            if max_depth not in generation_map:
                generation_map[max_depth] = []
            generation_map[max_depth].append(person)
        
        # Return generations in reverse order (oldest first)
        generations = []
        for depth in sorted(generation_map.keys(), reverse=True):
            generations.append(generation_map[depth])
        
        return generations
    
    def _max_descendant_depth(self, session, person_id: int, max_depth: int = 20) -> int:
        """Calculate maximum depth of descendants for a person."""
        queue = [(person_id, 0)]
        max_found_depth = 0
        visited = set()
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth >= max_depth or current_id in visited:
                continue
            
            visited.add(current_id)
            max_found_depth = max(max_found_depth, depth)
            
            # Get families where person is a parent
            families = session.query(FamilyORM).filter(
                (FamilyORM.father_id == current_id) | 
                (FamilyORM.mother_id == current_id)
            ).all()
            
            for family in families:
                children = session.query(PersonORM).filter(
                    PersonORM.parent_family_id == family.id
                ).all()
                
                for child in children:
                    if child.id not in visited:
                        queue.append((child.id, depth + 1))
        
        return max_found_depth
    
    def find_relationship_type(self, session, person1_id: int, person2_id: int) -> str:
        """
        Determine the relationship type between two persons.
        Returns human-readable relationship description.
        """
        if person1_id == person2_id:
            return "same person"
        
        # Check for direct parent-child relationship
        person1 = session.query(PersonORM).filter(PersonORM.id == person1_id).first()
        person2 = session.query(PersonORM).filter(PersonORM.id == person2_id).first()
        
        if not person1 or not person2:
            return "unknown"
        
        # Check if person1 is parent of person2
        if (person2.parent_family and 
            (person2.parent_family.father_id == person1_id or 
             person2.parent_family.mother_id == person1_id)):
            return "parent-child"
        
        # Check if person2 is parent of person1
        if (person1.parent_family and 
            (person1.parent_family.father_id == person2_id or 
             person1.parent_family.mother_id == person2_id)):
            return "child-parent"
        
        # Check for sibling relationship
        if (person1.parent_family and person2.parent_family and 
            person1.parent_family.id == person2.parent_family.id):
            return "siblings"
        
        # Check for more distant relationships
        relationship_info = self.calculate_relationship_distance(session, person1_id, person2_id)
        
        if relationship_info is None:
            return "not related"
        
        ancestor_id, dist1, dist2 = relationship_info
        
        # Determine relationship type based on distances
        if dist1 == 1 and dist2 == 1:
            return "siblings"
        elif dist1 == 1 and dist2 == 2:
            return "aunt/uncle - nephew/niece"
        elif dist1 == 2 and dist2 == 1:
            return "nephew/niece - aunt/uncle"
        elif dist1 == 2 and dist2 == 2:
            return "cousins"
        elif dist1 == 1:
            return f"grandparent-grandchild ({dist2-1} generations)"
        elif dist2 == 1:
            return f"grandchild-grandparent ({dist1-1} generations)"
        else:
            return f"distant relatives ({dist1}, {dist2})"
    
    def detect_data_inconsistencies(self, session) -> List[Dict[str, Any]]:
        """Detect various data inconsistencies in the database."""
        inconsistencies = []
        
        # Check for impossible birth/death date combinations
        persons = session.query(PersonORM).all()
        
        for person in persons:
            # Check for birth after death
            if (person.birth_event and person.death_event and 
                person.birth_event.date and person.death_event.date and
                person.birth_event.date.year and person.death_event.date.year):
                
                if person.birth_event.date.year > person.death_event.date.year:
                    inconsistencies.append({
                        'type': 'impossible_dates',
                        'person_id': person.id,
                        'description': f"Birth year ({person.birth_event.date.year}) after death year ({person.death_event.date.year})",
                        'severity': 'high'
                    })
            
            # Check for unrealistic ages
            if person.birth_event and person.birth_event.date and person.birth_event.date.year:
                current_year = 2024  # Could be datetime.now().year
                age = current_year - person.birth_event.date.year
                
                if age > 150:
                    inconsistencies.append({
                        'type': 'unrealistic_age',
                        'person_id': person.id,
                        'description': f"Person would be {age} years old",
                        'severity': 'medium'
                    })
        
        # Check for families with impossible relationships
        families = session.query(FamilyORM).all()
        
        for family in families:
            if family.father_id and family.mother_id:
                father = session.query(PersonORM).filter(PersonORM.id == family.father_id).first()
                mother = session.query(PersonORM).filter(PersonORM.id == family.mother_id).first()
                
                if father and mother:
                    # Check for same-sex marriages (if desired)
                    if father.sex == mother.sex and father.sex != Sex.NEUTER:
                        inconsistencies.append({
                            'type': 'same_sex_marriage',
                            'family_id': family.id,
                            'description': f"Same sex marriage: {father.sex.value}",
                            'severity': 'low'
                        })
        
        return inconsistencies
    
    def suggest_potential_matches(self, session, person_id: int, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Suggest potential duplicate persons based on name similarity and dates.
        """
        target_person = session.query(PersonORM).filter(PersonORM.id == person_id).first()
        if not target_person:
            return []
        
        # Find persons with similar names
        candidates = session.query(PersonORM).filter(
            PersonORM.id != person_id,
            PersonORM.surname.ilike(f"%{target_person.surname}%")
        ).all()
        
        matches = []
        
        for candidate in candidates:
            similarity = self._calculate_person_similarity(target_person, candidate)
            
            if similarity >= threshold:
                matches.append({
                    'person_id': candidate.id,
                    'similarity': similarity,
                    'first_name': candidate.first_name,
                    'surname': candidate.surname,
                    'reasons': self._get_similarity_reasons(target_person, candidate)
                })
        
        # Sort by similarity score
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches
    
    def _calculate_person_similarity(self, person1: PersonORM, person2: PersonORM) -> float:
        """Calculate similarity score between two persons (0.0 to 1.0)."""
        score = 0.0
        factors = 0
        
        # Name similarity
        if person1.first_name and person2.first_name:
            name_sim = self._string_similarity(person1.first_name, person2.first_name)
            score += name_sim * 0.4
            factors += 0.4
        
        if person1.surname and person2.surname:
            surname_sim = self._string_similarity(person1.surname, person2.surname)
            score += surname_sim * 0.4
            factors += 0.4
        
        # Sex match
        if person1.sex == person2.sex:
            score += 0.2
        factors += 0.2
        
        # Birth date similarity (if available)
        # This would require implementing date comparison logic
        
        return score / factors if factors > 0 else 0.0
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using simple metrics."""
        if not str1 or not str2:
            return 0.0
        
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        if str1_lower == str2_lower:
            return 1.0
        
        # Simple edit distance approximation
        longer = str1_lower if len(str1_lower) >= len(str2_lower) else str2_lower
        shorter = str2_lower if len(str2_lower) < len(str1_lower) else str1_lower
        
        if len(longer) == 0:
            return 1.0
        
        edit_distance = self._levenshtein_distance(str1_lower, str2_lower)
        similarity = (len(longer) - edit_distance) / len(longer)
        
        return max(0.0, similarity)
    
    def _levenshtein_distance(self, str1: str, str2: str) -> int:
        """Calculate Levenshtein edit distance between two strings."""
        if len(str1) < len(str2):
            return self._levenshtein_distance(str2, str1)
        
        if len(str2) == 0:
            return len(str1)
        
        previous_row = list(range(len(str2) + 1))
        for i, char1 in enumerate(str1):
            current_row = [i + 1]
            for j, char2 in enumerate(str2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (char1 != char2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _get_similarity_reasons(self, person1: PersonORM, person2: PersonORM) -> List[str]:
        """Get list of reasons why two persons might be similar."""
        reasons = []
        
        if person1.first_name and person2.first_name:
            name_sim = self._string_similarity(person1.first_name, person2.first_name)
            if name_sim > 0.8:
                reasons.append(f"Similar first names: {person1.first_name} / {person2.first_name}")
        
        if person1.surname and person2.surname:
            surname_sim = self._string_similarity(person1.surname, person2.surname)
            if surname_sim > 0.8:
                reasons.append(f"Similar surnames: {person1.surname} / {person2.surname}")
        
        if person1.sex == person2.sex and person1.sex != Sex.NEUTER:
            reasons.append(f"Same sex: {person1.sex.value}")
        
        return reasons
    
    def get_statistics(self, session) -> Dict[str, Any]:
        """Get comprehensive statistics about the genealogy database."""
        from sqlalchemy import func
        from .models import Sex, EventType
        from .database import EventORM
        
        stats = {}
        
        # Basic counts
        stats['total_persons'] = session.query(PersonORM).count()
        stats['total_families'] = session.query(FamilyORM).count()
        
        # Gender distribution
        stats['male_count'] = session.query(PersonORM).filter(PersonORM.sex == Sex.MALE).count()
        stats['female_count'] = session.query(PersonORM).filter(PersonORM.sex == Sex.FEMALE).count()
        stats['unknown_gender'] = session.query(PersonORM).filter(
            (PersonORM.sex == Sex.NEUTER) | (PersonORM.sex.is_(None))
        ).count()
        
        # Birth/Death records - using EXISTS queries instead of relationship operators
        from sqlalchemy import exists
        from .database import EventORM
        
        stats['persons_with_birth_date'] = session.query(PersonORM).filter(
            exists().where(EventORM.birth_person_id == PersonORM.id)
        ).count()
        stats['persons_with_death_date'] = session.query(PersonORM).filter(
            exists().where(EventORM.death_person_id == PersonORM.id)
        ).count()
        
        # Date ranges - using direct EventORM queries to avoid relation issues
        try:
            # Get birth events directly
            birth_events = session.query(EventORM).filter(
                EventORM.birth_person_id.isnot(None),
                EventORM.date_id.isnot(None)
            ).all()
            
            if birth_events:
                years = []
                for event in birth_events:
                    try:
                        if event.date and hasattr(event.date, 'year') and event.date.year:
                            year = event.date.year
                            if 1000 <= year <= 2100:  # Sanity check
                                years.append(year)
                    except Exception:
                        continue  # Skip problematic events
                
                if years:
                    stats['earliest_birth_year'] = min(years)
                    stats['latest_birth_year'] = max(years)
        except Exception as e:
            print(f"Error getting birth years: {e}")
            pass
        
        try:
            # Get death events directly
            death_events = session.query(EventORM).filter(
                EventORM.death_person_id.isnot(None),
                EventORM.date_id.isnot(None)
            ).all()
            
            if death_events:
                years = []
                for event in death_events:
                    try:
                        if event.date and hasattr(event.date, 'year') and event.date.year:
                            year = event.date.year
                            if 1000 <= year <= 2100:  # Sanity check
                                years.append(year)
                    except Exception:
                        continue  # Skip problematic events
                
                if years:
                    stats['earliest_death_year'] = min(years)
                    stats['latest_death_year'] = max(years)
        except Exception as e:
            print(f"Error getting death years: {e}")
            pass
        
        # Family statistics
        families_with_children = session.query(FamilyORM).join(
            PersonORM, PersonORM.parent_family_id == FamilyORM.id
        ).distinct().count()
        stats['families_with_children'] = families_with_children
        
        # Average children per family
        if stats['total_families'] > 0:
            total_children = session.query(PersonORM).filter(
                PersonORM.parent_family_id.isnot(None)
            ).count()
            stats['average_children'] = total_children / stats['total_families']
        else:
            stats['average_children'] = 0
        
        # Largest family
        if stats['total_families'] > 0:
            family_sizes = session.query(
                FamilyORM.id,
                func.count(PersonORM.id).label('child_count')
            ).outerjoin(
                PersonORM, PersonORM.parent_family_id == FamilyORM.id
            ).group_by(FamilyORM.id).all()
            
            if family_sizes:
                stats['largest_family_size'] = max(size[1] for size in family_sizes)
            else:
                stats['largest_family_size'] = 0
        else:
            stats['largest_family_size'] = 0
        
        # Most common surnames
        surname_counts = session.query(
            PersonORM.surname,
            func.count(PersonORM.id).label('count')
        ).filter(
            PersonORM.surname.isnot(None),
            PersonORM.surname != ''
        ).group_by(PersonORM.surname).order_by(
            func.count(PersonORM.id).desc()
        ).limit(20).all()
        
        stats['most_common_surnames'] = [(surname, count) for surname, count in surname_counts]
        
        # Calculate generations (simplified approach)
        try:
            max_depth = 0
            # Find all persons without parents (roots)
            roots = session.query(PersonORM).filter(
                PersonORM.parent_family_id.is_(None)
            ).all()
            
            for root in roots:
                depth = self._calculate_max_depth(session, root.id, 0)
                max_depth = max(max_depth, depth)
            
            stats['generations'] = max_depth + 1
        except Exception:
            stats['generations'] = 0
        
        # Living vs deceased
        stats['living_persons'] = stats['total_persons'] - stats['persons_with_death_date']
        
        # Data quality metrics - using EXISTS for birth events with dates and places
        stats['persons_with_complete_birth_info'] = session.query(PersonORM).filter(
            exists().where(
                (EventORM.birth_person_id == PersonORM.id) &
                (EventORM.date_id.isnot(None)) &
                (EventORM.place_id.isnot(None))
            )
        ).count()
        
        stats['persons_with_occupation'] = session.query(PersonORM).filter(
            PersonORM.occupation.isnot(None),
            PersonORM.occupation != ''
        ).count()
        
        # Last update timestamp
        try:
            from datetime import datetime
            stats['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            stats['last_update'] = None
        
        return stats
    
    def _calculate_max_depth(self, session, person_id: int, current_depth: int) -> int:
        """Calculate maximum generation depth from a given person."""
        # Get children of this person
        children = session.query(PersonORM).join(
            FamilyORM, (FamilyORM.father_id == person_id) | (FamilyORM.mother_id == person_id)
        ).filter(
            PersonORM.parent_family_id == FamilyORM.id
        ).all()
        
        if not children:
            return current_depth
        
        max_child_depth = current_depth
        for child in children:
            child_depth = self._calculate_max_depth(session, child.id, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth

    # ============================================================================
    # ADVANCED CONSANGUINITY METHODS (TDD Implementation)
    # ============================================================================
    
    def calculate_consanguinity_advanced(self, session, person_id: int) -> ConsanguinityResult:
        """
        Algorithme avancé de calcul de consanguinité basé sur l'algorithme de Didier Rémy.
        
        Utilise un tri topologique pour garantir un ordre de calcul correct et 
        gère les cas complexes avec chemins multiples et boucles.
        
        Args:
            session: Session SQLAlchemy
            person_id: ID de la personne
            
        Returns:
            ConsanguinityResult avec le coefficient de consanguinité calculé
            
        Raises:
            ValueError: Si une boucle généalogique est détectée
        """
        # Détecter les boucles avant de commencer le calcul
        if self._person_has_loop(session, person_id, set()):
            raise ValueError(f"Boucle détectée dans l'arbre généalogique pour la personne {person_id}")
        
        # Vérifier le cache
        if person_id in self._consanguinity_cache:
            self._cache_hits += 1
            cached_value = self._consanguinity_cache[person_id]
            return ConsanguinityResult(
                person_id=person_id,
                consanguinity=cached_value,
                relationship_paths=[],
                common_ancestors=set()
            )
        else:
            self._cache_misses += 1
        
        person = session.query(PersonORM).filter(PersonORM.id == person_id).first()
        if not person or not person.parent_family:
            result = ConsanguinityResult(
                person_id=person_id,
                consanguinity=0.0,
                relationship_paths=[],
                common_ancestors=set()
            )
            self._consanguinity_cache[person_id] = 0.0
            return result
        
        family = person.parent_family
        
        if not family.father_id or not family.mother_id:
            result = ConsanguinityResult(
                person_id=person_id,
                consanguinity=0.0,
                relationship_paths=[],
                common_ancestors=set()
            )
            self._consanguinity_cache[person_id] = 0.0
            return result
        
        # Trouver les ancêtres communs entre les parents
        common_ancestors = self.find_common_ancestors(session, family.father_id, family.mother_id)
        
        if not common_ancestors:
            result = ConsanguinityResult(
                person_id=person_id,
                consanguinity=0.0,
                relationship_paths=[],
                common_ancestors=set()
            )
            self._consanguinity_cache[person_id] = 0.0
            return result
        
        # Calculer la consanguinité selon l'algorithme classique amélioré
        total_consanguinity = 0.0
        relationship_paths = []
        
        for ancestor_id in common_ancestors:
            father_distance = self._distance_to_ancestor(session, family.father_id, ancestor_id)
            mother_distance = self._distance_to_ancestor(session, family.mother_id, ancestor_id)
            
            if father_distance is not None and mother_distance is not None:
                # Consanguinité contribution de ce chemin
                # Formule: (1/2)^(n1 + n2 + 1) où n1, n2 sont les distances à l'ancêtre commun
                path_consanguinity = (0.5) ** (father_distance + mother_distance + 1)
                
                # Prendre en compte la consanguinité de l'ancêtre commun
                # Seulement si l'ancêtre n'est pas en cours de calcul (éviter récursion)
                ancestor_consanguinity = 0.0
                if ancestor_id not in self._consanguinity_cache:
                    # Marquer temporairement l'ancêtre comme en cours de calcul
                    self._consanguinity_cache[ancestor_id] = 0.0
                    ancestor_result = self.calculate_consanguinity_advanced(session, ancestor_id)
                    ancestor_consanguinity = ancestor_result.consanguinity
                    self._consanguinity_cache[ancestor_id] = ancestor_consanguinity
                else:
                    ancestor_consanguinity = self._consanguinity_cache[ancestor_id]
                
                path_consanguinity *= (1 + ancestor_consanguinity)
                total_consanguinity += path_consanguinity
                
                relationship_paths.append(RelationshipPath(
                    person1_id=family.father_id,
                    person2_id=family.mother_id,
                    common_ancestor_id=ancestor_id,
                    person1_distance=father_distance,
                    person2_distance=mother_distance,
                    path_type='mixed',
                    person1_path=[],  # Chemins détaillés non nécessaires pour consanguinité
                    person2_path=[],
                    relationship_name=f"Ancêtre commun (distance {father_distance}+{mother_distance})"
                ))
        
        # Mettre en cache
        self._consanguinity_cache[person_id] = total_consanguinity
        
        result = ConsanguinityResult(
            person_id=person_id,
            consanguinity=total_consanguinity,
            relationship_paths=relationship_paths,
            common_ancestors=common_ancestors
        )
        
        return result
    
    def _get_consanguinity_recursive(self, session, person_id: int) -> float:
        """Obtenir la consanguinité d'une personne de manière récursive."""
        if person_id in self._consanguinity_cache:
            return self._consanguinity_cache[person_id]
        
        # Calculer récursivement
        result = self.calculate_consanguinity_advanced(session, person_id)
        return result.consanguinity
    
    def _calculate_kinship_coefficient(self, session, person1_id: int, person2_id: int) -> float:
        """
        Calcule le coefficient de parenté PHI(X,Y) entre deux personnes.
        
        PHI(X,Y) = probabilité qu'un allèle pris au hasard chez X soit 
        identique par descendance à un allèle pris au hasard chez Y.
        """
        if person1_id == person2_id:
            # PHI(X,X) = (1 + F(X)) / 2
            consanguinity = self._get_consanguinity_recursive(session, person1_id)
            return (1 + consanguinity) / 2
        
        # Cas de base : pas d'ancêtres communs
        common_ancestors = self.find_common_ancestors(session, person1_id, person2_id)
        if not common_ancestors:
            return 0.0
        
        total_kinship = 0.0
        
        for ancestor_id in common_ancestors:
            dist1 = self._distance_to_ancestor(session, person1_id, ancestor_id)
            dist2 = self._distance_to_ancestor(session, person2_id, ancestor_id)
            
            if dist1 is not None and dist2 is not None:
                # Contribution de ce chemin au coefficient de parenté
                # PHI = (1/2)^(d1 + d2) * (1 + F(ancêtre))
                ancestor_consanguinity = self._get_consanguinity_recursive(session, ancestor_id)
                path_kinship = (0.5) ** (dist1 + dist2) * (1 + ancestor_consanguinity)
                total_kinship += path_kinship
        
        return total_kinship
    
    def topological_sort_persons(self, session) -> List[PersonORM]:
        """
        Trie les personnes par ordre topologique (ancêtres avant descendants).
        
        Utilise l'algorithme de Kahn pour garantir que chaque personne 
        est traitée après ses ancêtres.
        
        Returns:
            Liste des personnes triées par ordre générationnel
        """
        # Obtenir toutes les personnes
        all_persons = session.query(PersonORM).all()
        
        # Construire le graphe de dépendances : enfant -> parents
        in_degree = {person.id: 0 for person in all_persons}
        graph = {person.id: [] for person in all_persons}
        
        for person in all_persons:
            if person.parent_family:
                parents = []
                if person.parent_family.father_id:
                    parents.append(person.parent_family.father_id)
                if person.parent_family.mother_id:
                    parents.append(person.parent_family.mother_id)
                
                # Chaque personne dépend de ses parents
                in_degree[person.id] = len(parents)
                
                # Ajouter les arcs des parents vers l'enfant
                for parent_id in parents:
                    if parent_id in graph:
                        graph[parent_id].append(person.id)
        
        # Algorithme de Kahn
        queue = deque()
        
        # Commencer par les personnes sans parents (racines)
        for person_id, degree in in_degree.items():
            if degree == 0:
                queue.append(person_id)
        
        sorted_ids = []
        
        while queue:
            current_id = queue.popleft()
            sorted_ids.append(current_id)
            
            # Réduire le degré d'entrée des descendants
            for descendant_id in graph[current_id]:
                in_degree[descendant_id] -= 1
                if in_degree[descendant_id] == 0:
                    queue.append(descendant_id)
        
        # Vérifier s'il y a des cycles
        if len(sorted_ids) != len(all_persons):
            # Il y a des cycles, les inclure à la fin
            remaining_ids = set(person.id for person in all_persons) - set(sorted_ids)
            sorted_ids.extend(remaining_ids)
        
        # Retourner les objets PersonORM dans l'ordre trié
        id_to_person = {person.id: person for person in all_persons}
        return [id_to_person[person_id] for person_id in sorted_ids if person_id in id_to_person]
    
    def detect_genealogical_loops(self, session) -> bool:
        """
        Détecte la présence de boucles dans l'arbre généalogique.
        
        Une boucle est détectée si une personne est son propre ancêtre,
        ce qui est impossible en réalité mais peut arriver dans les données.
        
        Returns:
            True s'il y a des boucles, False sinon
        """
        all_persons = session.query(PersonORM).all()
        
        for person in all_persons:
            if self._has_loop_from_person(session, person.id, set()):
                return True
        
        return False
    
    def _has_loop_from_person(self, session, person_id: int, visited: Set[int]) -> bool:
        """
        Vérifie s'il y a une boucle en partant d'une personne donnée.
        
        Utilise un parcours en profondeur avec détection de cycle.
        """
        if person_id in visited:
            return True  # Cycle détecté
        
        person = session.query(PersonORM).filter(PersonORM.id == person_id).first()
        if not person or not person.parent_family:
            return False
        
        # Ajouter à la pile de visite
        visited.add(person_id)
        
        # Vérifier récursivement les parents
        has_loop = False
        
        if person.parent_family.father_id:
            has_loop |= self._has_loop_from_person(session, person.parent_family.father_id, visited.copy())
        
        if person.parent_family.mother_id and not has_loop:
            has_loop |= self._has_loop_from_person(session, person.parent_family.mother_id, visited.copy())
        
        return has_loop
    
    def _person_has_loop(self, session, person_id: int, visited: Set[int]) -> bool:
        """
        Vérifie si une personne spécifique a une boucle dans son arbre généalogique.
        
        Version optimisée pour une seule personne.
        """
        return self._has_loop_from_person(session, person_id, visited)
    
    def compute_all_consanguinity_advanced(self, session, from_scratch: bool = False, verbosity: int = 1) -> Dict[int, float]:
        """
        Calcule la consanguinité pour toutes les personnes en utilisant l'algorithme avancé.
        
        Utilise le tri topologique pour garantir un ordre de calcul optimal
        et optimise avec un système de cache.
        
        Args:
            session: Session SQLAlchemy
            from_scratch: Si True, recalcule même les valeurs existantes
            verbosity: Niveau de verbosité (0=silencieux, 1=normal, 2=détaillé)
            
        Returns:
            Dictionnaire person_id -> coefficient de consanguinité
        """
        if verbosity > 0:
            print("=== Calcul de consanguinité avancé ===")
        
        # Détecter les boucles avant de commencer
        if self.detect_genealogical_loops(session):
            if verbosity > 0:
                print("⚠️  Boucles détectées dans l'arbre généalogique!")
        
        # Clear cache if from_scratch
        if from_scratch:
            self.clear_consanguinity_cache()
        
        # Tri topologique des personnes
        if verbosity > 1:
            print("Tri topologique des personnes...")
        
        sorted_persons = self.topological_sort_persons(session)
        total_persons = len(sorted_persons)
        
        if verbosity > 0:
            print(f"Traitement de {total_persons} personnes...")
        
        results = {}
        processed = 0
        
        for i, person in enumerate(sorted_persons):
            # Progress reporting
            if verbosity > 1 and i % 100 == 0:
                print(f"  Progression: {i}/{total_persons} ({i/total_persons*100:.1f}%)")
            
            # Calculer la consanguinité
            if from_scratch or person.consang == 0.0:
                result = self.calculate_consanguinity_advanced(session, person.id)
                person.consang = result.consanguinity
                results[person.id] = result.consanguinity
                processed += 1
            else:
                results[person.id] = person.consang
        
        # Sauvegarder en base
        session.commit()
        
        if verbosity > 0:
            print(f"✅ Traitement terminé : {processed} nouveaux calculs")
            if verbosity > 1:
                # Statistiques
                non_zero = sum(1 for v in results.values() if v > 0)
                max_consang = max(results.values()) if results.values() else 0
                print(f"   - Personnes avec consanguinité > 0 : {non_zero}")
                print(f"   - Consanguinité maximale : {max_consang:.6f}")
        
        return results
    
    def clear_consanguinity_cache(self):
        """Vide le cache de consanguinité."""
        self._consanguinity_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        if hasattr(self, '_kinship_cache'):
            self._kinship_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Retourne les statistiques du cache."""
        return {
            'consanguinity_cache_size': len(self._consanguinity_cache),
            'ancestor_cache_size': len(self._ancestor_cache),
            'descendant_cache_size': len(self._descendant_cache),
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'hit_rate': self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0.0
        }
    
    # =====================================================
    # NAVIGATION GÉNÉALOGIQUE ET LIENS FAMILIAUX
    # =====================================================
    
    def find_detailed_relationship_paths(self, session, person1_id: int, person2_id: int) -> List[RelationshipPath]:
        """
        Trouve tous les chemins détaillés entre deux personnes avec les ancêtres communs.
        
        Args:
            session: Session SQLAlchemy
            person1_id: ID de la première personne
            person2_id: ID de la deuxième personne
            
        Returns:
            Liste des chemins de parenté détaillés
        """
        if person1_id == person2_id:
            return []
        
        # Trouver les ancêtres communs
        common_ancestors = self.find_common_ancestors(session, person1_id, person2_id)
        
        if not common_ancestors:
            return []
        
        paths = []
        
        for ancestor_id in common_ancestors:
            # Calculer les chemins détaillés vers l'ancêtre commun
            path1 = self._build_path_to_ancestor(session, person1_id, ancestor_id)
            path2 = self._build_path_to_ancestor(session, person2_id, ancestor_id)
            
            if path1 and path2:
                # Déterminer le type de chemin (paternel, maternel, mixte)
                path_type = self._determine_path_type(path1, path2)
                
                # Générer le nom de la relation
                relationship_name = self._generate_relationship_name(len(path1), len(path2))
                
                path = RelationshipPath(
                    person1_id=person1_id,
                    person2_id=person2_id,
                    common_ancestor_id=ancestor_id,
                    person1_distance=len(path1),
                    person2_distance=len(path2),
                    path_type=path_type,
                    person1_path=path1,
                    person2_path=path2,
                    relationship_name=relationship_name
                )
                paths.append(path)
        
        # Trier par distance totale (chemins les plus courts en premier)
        paths.sort(key=lambda p: p.person1_distance + p.person2_distance)
        
        return paths
    
    def _build_path_to_ancestor(self, session, person_id: int, ancestor_id: int) -> List[FamilyLink]:
        """
        Construit le chemin détaillé d'une personne vers un ancêtre.
        
        Args:
            session: Session SQLAlchemy
            person_id: ID de la personne de départ
            ancestor_id: ID de l'ancêtre cible
            
        Returns:
            Liste des liens familiaux formant le chemin
        """
        if person_id == ancestor_id:
            return []
        
        # Recherche en largeur pour trouver le chemin le plus court
        queue = [(person_id, [])]
        visited = set()
        
        while queue:
            current_id, path = queue.pop(0)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id == ancestor_id:
                return path
            
            # Obtenir les parents
            person = session.query(PersonORM).filter(PersonORM.id == current_id).first()
            if not person or not person.parent_family:
                continue
            
            family = person.parent_family
            
            # Ajouter le père au chemin
            if family.father_id and family.father_id not in visited:
                new_link = FamilyLink(
                    person_id=family.father_id,
                    relation_type=RelationType.PARENT,
                    distance=len(path) + 1,
                    is_paternal=True
                )
                queue.append((family.father_id, path + [new_link]))
            
            # Ajouter la mère au chemin
            if family.mother_id and family.mother_id not in visited:
                new_link = FamilyLink(
                    person_id=family.mother_id,
                    relation_type=RelationType.PARENT,
                    distance=len(path) + 1,
                    is_paternal=False
                )
                queue.append((family.mother_id, path + [new_link]))
        
        return []
    
    def _determine_path_type(self, path1: List[FamilyLink], path2: List[FamilyLink]) -> str:
        """Détermine le type de chemin généalogique."""
        if not path1 or not path2:
            return "unknown"
        
        # Vérifier si les chemins sont purement paternels ou maternels
        path1_paternal = all(link.is_paternal for link in path1)
        path1_maternal = all(not link.is_paternal for link in path1)
        path2_paternal = all(link.is_paternal for link in path2)
        path2_maternal = all(not link.is_paternal for link in path2)
        
        if path1_paternal and path2_paternal:
            return "paternal"
        elif path1_maternal and path2_maternal:
            return "maternal"
        else:
            return "mixed"
    
    def _generate_relationship_name(self, distance1: int, distance2: int) -> str:
        """
        Génère un nom de relation humainement lisible basé sur les distances.
        
        Args:
            distance1: Distance de la personne 1 à l'ancêtre commun
            distance2: Distance de la personne 2 à l'ancêtre commun
            
        Returns:
            Nom de la relation
        """
        if distance1 == 0 and distance2 == 0:
            return "Même personne"
        elif distance1 == 0:
            if distance2 == 1:
                return "Parent/Enfant"
            elif distance2 == 2:
                return "Grand-parent/Petit-enfant"
            elif distance2 == 3:
                return "Arrière-grand-parent/Arrière-petit-enfant"
            else:
                return f"Ancêtre/Descendant ({distance2} générations)"
        elif distance2 == 0:
            if distance1 == 1:
                return "Enfant/Parent"
            elif distance1 == 2:
                return "Petit-enfant/Grand-parent"
            elif distance1 == 3:
                return "Arrière-petit-enfant/Arrière-grand-parent"
            else:
                return f"Descendant/Ancêtre ({distance1} générations)"
        elif distance1 == 1 and distance2 == 1:
            return "Frères/Sœurs"
        elif distance1 == 2 and distance2 == 2:
            return "Cousins germains"
        elif distance1 == 3 and distance2 == 3:
            return "Cousins issus de germains"
        elif distance1 == 2 and distance2 == 3:
            return "Cousin et petit-cousin"
        elif distance1 == 3 and distance2 == 2:
            return "Petit-cousin et cousin"
        elif distance1 == 1 and distance2 == 2:
            return "Oncle/Tante et Neveu/Nièce"
        elif distance1 == 2 and distance2 == 1:
            return "Neveu/Nièce et Oncle/Tante"
        elif min(distance1, distance2) == 1:
            max_dist = max(distance1, distance2)
            return f"Oncle/Tante à la {max_dist-1}e génération"
        else:
            cousin_degree = min(distance1, distance2) - 1
            removed = abs(distance1 - distance2)
            if removed == 0:
                if cousin_degree == 1:
                    return "Cousins germains"
                elif cousin_degree == 2:
                    return "Cousins issus de germains"
                else:
                    return f"Cousins au {cousin_degree}e degré"
            else:
                return f"Cousins au {cousin_degree}e degré, {removed} fois enlevés"
    
    def find_relationship_summary(self, session, person1_id: int, person2_id: int) -> Optional[RelationshipSummary]:
        """
        Trouve un résumé complet de la relation entre deux personnes.
        
        Args:
            session: Session SQLAlchemy
            person1_id: ID de la première personne
            person2_id: ID de la deuxième personne
            
        Returns:
            Résumé de la relation ou None si pas de relation
        """
        if person1_id == person2_id:
            return RelationshipSummary(
                person1_id=person1_id,
                person2_id=person2_id,
                primary_relationship=RelationType.SELF,
                relationship_description="Même personne",
                consanguinity=0.0,
                paths=[],
                common_ancestors=[],
                closest_common_ancestor=None
            )
        
        # Trouver tous les chemins détaillés
        paths = self.find_detailed_relationship_paths(session, person1_id, person2_id)
        
        if not paths:
            return None
        
        # Déterminer la relation principale (chemin le plus court)
        primary_path = paths[0]
        primary_relationship = self._classify_relationship(
            primary_path.person1_distance, 
            primary_path.person2_distance
        )
        
        # Calculer la consanguinité si les personnes sont apparentées
        common_ancestors = list(set(path.common_ancestor_id for path in paths))
        consanguinity = 0.0
        
        if common_ancestors:
            # Calculer la consanguinité entre les deux personnes
            result1 = self.calculate_consanguinity_advanced(session, person1_id)
            result2 = self.calculate_consanguinity_advanced(session, person2_id)
            
            # Pour une estimation de la consanguinité entre les deux personnes,
            # on peut utiliser le coefficient du chemin le plus court
            if primary_path.person1_distance > 0 and primary_path.person2_distance > 0:
                consanguinity = 0.5 ** (primary_path.person1_distance + primary_path.person2_distance)
        
        return RelationshipSummary(
            person1_id=person1_id,
            person2_id=person2_id,
            primary_relationship=primary_relationship,
            relationship_description=primary_path.relationship_name,
            consanguinity=consanguinity,
            paths=paths,
            common_ancestors=common_ancestors,
            closest_common_ancestor=primary_path.common_ancestor_id
        )
    
    def _classify_relationship(self, distance1: int, distance2: int) -> RelationType:
        """Classifie le type de relation basé sur les distances."""
        if distance1 == 0 and distance2 == 0:
            return RelationType.SELF
        elif distance1 == 0 and distance2 == 1:
            return RelationType.PARENT
        elif distance1 == 1 and distance2 == 0:
            return RelationType.CHILD
        elif distance1 == 1 and distance2 == 1:
            return RelationType.SIBLING
        elif distance1 == 0 and distance2 == 2:
            return RelationType.GRANDPARENT
        elif distance1 == 2 and distance2 == 0:
            return RelationType.GRANDCHILD
        elif distance1 == 0 and distance2 >= 3:
            return RelationType.GREAT_GRANDPARENT
        elif distance1 >= 3 and distance2 == 0:
            return RelationType.GREAT_GRANDCHILD
        elif distance1 == 1 and distance2 == 2:
            return RelationType.UNCLE_AUNT
        elif distance1 == 2 and distance2 == 1:
            return RelationType.NEPHEW_NIECE
        elif distance1 == 2 and distance2 == 2:
            return RelationType.COUSIN
        elif (distance1 == 2 and distance2 == 3) or (distance1 == 3 and distance2 == 2):
            return RelationType.COUSIN_ONCE_REMOVED
        elif (distance1 == 2 and distance2 == 4) or (distance1 == 4 and distance2 == 2):
            return RelationType.COUSIN_TWICE_REMOVED
        else:
            return RelationType.DISTANT_RELATIVE
    
    def get_person_family_context(self, session, person_id: int) -> Dict[str, Any]:
        """
        Obtient le contexte familial complet d'une personne.
        
        Args:
            session: Session SQLAlchemy
            person_id: ID de la personne
            
        Returns:
            Dictionnaire avec toutes les informations familiales
        """
        person = session.query(PersonORM).filter(PersonORM.id == person_id).first()
        if not person:
            return {}
        
        context = {
            'person': person,
            'parents': [],
            'children': [],
            'siblings': [],
            'spouses': [],
            'grandparents': [],
            'grandchildren': [],
            'uncles_aunts': [],
            'nephews_nieces': [],
            'cousins': []
        }
        
        # Parents
        if person.parent_family:
            if person.parent_family.father:
                context['parents'].append(person.parent_family.father)
            if person.parent_family.mother:
                context['parents'].append(person.parent_family.mother)
        
        # Enfants
        children = session.query(PersonORM).filter(PersonORM.parent_family_id.in_(
            session.query(FamilyORM.id).filter(
                (FamilyORM.father_id == person_id) | (FamilyORM.mother_id == person_id)
            )
        )).all()
        context['children'] = children
        
        # Frères et sœurs
        if person.parent_family:
            siblings = session.query(PersonORM).filter(
                PersonORM.parent_family_id == person.parent_family_id,
                PersonORM.id != person_id
            ).all()
            context['siblings'] = siblings
        
        # Conjoints (approximation basée sur les familles partagées)
        spouse_families = session.query(FamilyORM).filter(
            (FamilyORM.father_id == person_id) | (FamilyORM.mother_id == person_id)
        ).all()
        
        spouses = []
        for family in spouse_families:
            if family.father_id == person_id and family.mother:
                spouses.append(family.mother)
            elif family.mother_id == person_id and family.father:
                spouses.append(family.father)
        context['spouses'] = spouses
        
        # Grands-parents
        grandparents = []
        for parent in context['parents']:
            if parent.parent_family:
                if parent.parent_family.father:
                    grandparents.append(parent.parent_family.father)
                if parent.parent_family.mother:
                    grandparents.append(parent.parent_family.mother)
        context['grandparents'] = grandparents
        
        # Petits-enfants
        grandchildren = []
        for child in children:
            child_families = session.query(FamilyORM).filter(
                (FamilyORM.father_id == child.id) | (FamilyORM.mother_id == child.id)
            ).all()
            for family in child_families:
                grandchildren.extend(session.query(PersonORM).filter(
                    PersonORM.parent_family_id == family.id
                ).all())
        context['grandchildren'] = grandchildren
        
        return context