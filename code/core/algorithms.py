"""
Genealogical algorithms for GeneWeb Python implementation.

This module contains algorithms for consanguinity calculation, relationship
analysis, and other genealogy-specific computations ported from the original
OCaml implementation.
"""
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass
import math

from .models import Person, Family, Sex
from .database import PersonORM, FamilyORM, DatabaseManager


@dataclass
class RelationshipPath:
    """Represents a path between two persons through common ancestors."""
    person1_id: int
    person2_id: int
    common_ancestor_id: int
    person1_distance: int  # Distance from person1 to common ancestor
    person2_distance: int  # Distance from person2 to common ancestor
    path_type: str  # 'paternal', 'maternal', 'mixed'


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
    
    def clear_cache(self):
        """Clear internal caches."""
        self._ancestor_cache.clear()
        self._descendant_cache.clear()
    
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
                    path_type='mixed'
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