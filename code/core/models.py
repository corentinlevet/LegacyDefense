"""
Core data models for GeneWeb Python implementation.

These models represent the fundamental genealogical entities based on the 
original OCaml implementation in the GeneWeb project.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, validator
import math


class Sex(Enum):
    """Person's sex/gender."""
    MALE = "male"
    FEMALE = "female"
    NEUTER = "neuter"  # Used for unknown/unspecified


class DeathReason(Enum):
    """Reason for death."""
    KILLED = "killed"
    MURDERED = "murdered"
    EXECUTED = "executed"
    DISAPPEARED = "disappeared"
    UNSPECIFIED = "unspecified"


class RelationType(Enum):
    """Types of relationships between persons."""
    ADOPTION = "adoption"
    RECOGNITION = "recognition"
    CANDIDATE_PARENT = "candidate_parent"
    GOD_PARENT = "god_parent"
    FOSTER_PARENT = "foster_parent"


class Calendar(Enum):
    """Calendar systems for dates."""
    GREGORIAN = "gregorian"
    JULIAN = "julian"
    FRENCH = "french"
    HEBREW = "hebrew"


class DatePrecision(Enum):
    """Date precision indicators."""
    SURE = "sure"
    ABOUT = "about"
    MAYBE = "maybe"
    BEFORE = "before"
    AFTER = "after"
    OR_YEAR = "or_year"
    YEAR_INT = "year_int"


@dataclass
class Date:
    """Represents a genealogical date with various precision levels."""
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None
    precision: DatePrecision = DatePrecision.SURE
    calendar: Calendar = Calendar.GREGORIAN
    delta: Optional[int] = None  # For year intervals
    
    def __str__(self) -> str:
        """String representation of the date."""
        date_str = ""
        if self.year:
            if self.month:
                if self.day:
                    date_str = f"{self.day:02d}/{self.month:02d}/{self.year}"
                else:
                    date_str = f"{self.month:02d}/{self.year}"
            else:
                date_str = str(self.year)
        
        if self.precision != DatePrecision.SURE:
            date_str = f"{self.precision.value} {date_str}"
        
        return date_str.strip()


@dataclass
class Place:
    """Represents a geographical place."""
    place: str = ""
    town: str = ""
    township: str = ""
    county: str = ""
    state: str = ""
    country: str = ""
    
    def __str__(self) -> str:
        """String representation of the place."""
        parts = [p for p in [self.place, self.town, self.township, 
                           self.county, self.state, self.country] if p]
        return ", ".join(parts)


class EventType(Enum):
    """Types of person events."""
    BIRTH = "birth"
    BAPTISM = "baptism"
    DEATH = "death"
    BURIAL = "burial"
    CREMATION = "cremation"
    ACCOMPLISHMENT = "accomplishment"
    ACQUISITION = "acquisition"
    ADHESION = "adhesion"
    BAPTISM_LDS = "baptism_lds"
    BAR_MITZVAH = "bar_mitzvah"
    BAT_MITZVAH = "bat_mitzvah"
    BENEDICTION = "benediction"
    CHANGE_NAME = "change_name"
    CIRCUMCISION = "circumcision"
    CONFIRMATION = "confirmation"
    CONFIRMATION_LDS = "confirmation_lds"
    DECORATION = "decoration"
    DEMOBILISATION = "demobilisation"
    DIPLOMA = "diploma"
    DISTINCTION = "distinction"
    DOTATION = "dotation"
    DOTATION_LDS = "dotation_lds"
    EDUCATION = "education"
    ELECTION = "election"
    EMIGRATION = "emigration"
    EXCOMMUNICATION = "excommunication"
    FAMILY_LINK_LDS = "family_link_lds"
    FIRST_COMMUNION = "first_communion"
    FUNERAL = "funeral"
    GRADUATE = "graduate"
    HOSPITALISATION = "hospitalisation"
    ILLNESS = "illness"
    IMMIGRATION = "immigration"
    LIST_PASSENGER = "list_passenger"
    MILITARY_DISTINCTION = "military_distinction"
    MILITARY_PROMOTION = "military_promotion"
    MILITARY_SERVICE = "military_service"
    MOBILISATION = "mobilisation"
    NATURALISATION = "naturalisation"
    OCCUPATION = "occupation"
    ORDINATION = "ordination"
    PROPERTY = "property"
    RECENSEMENT = "recensement"
    RESIDENCE = "residence"
    RETIRED = "retired"
    SCELLENT_CHILD_LDS = "scellent_child_lds"
    SCELLENT_PARENT_LDS = "scellent_parent_lds"
    SCELLENT_SPOUSE_LDS = "scellent_spouse_lds"
    VENTILATION = "ventilation"
    WILL = "will"


@dataclass
class Event:
    """Represents a genealogical event."""
    event_type: EventType
    date: Optional[Date] = None
    place: Optional[Place] = None
    reason: str = ""
    note: str = ""
    source: str = ""
    witnesses: List[int] = field(default_factory=list)  # Person IDs


@dataclass
class Title:
    """Represents a title or nobility."""
    name: str
    title: str = ""
    fief: str = ""
    date_start: Optional[Date] = None
    date_end: Optional[Date] = None
    nth: Optional[int] = None


@dataclass
class Name:
    """Represents a person's name components."""
    first_name: str = ""
    surname: str = ""
    occ: int = 0  # Occurrence number for disambiguation
    public_name: str = ""
    qualifiers: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    first_names_aliases: List[str] = field(default_factory=list)
    surnames_aliases: List[str] = field(default_factory=list)


class Access(Enum):
    """Access levels for person visibility."""
    PUBLIC = "public"
    IFTITLES = "iftitles"
    PRIVATE = "private"


class WitnessKind(Enum):
    """Types of witnesses for events."""
    WITNESS = "witness"
    WITNESS_GODPARENT = "witness_godparent"
    WITNESS_OFFICER = "witness_officer"


@dataclass
class SosaNumber:
    """Represents a Sosa numbering for genealogical navigation."""
    value: int = 1
    
    def __str__(self) -> str:
        return str(self.value)
    
    def father(self) -> 'SosaNumber':
        """Get father's Sosa number (current * 2)."""
        return SosaNumber(self.value * 2)
    
    def mother(self) -> 'SosaNumber':
        """Get mother's Sosa number (current * 2 + 1)."""
        return SosaNumber(self.value * 2 + 1)
    
    def child(self) -> 'SosaNumber':
        """Get child's Sosa number (current // 2)."""
        return SosaNumber(self.value // 2)
    
    def generation(self) -> int:
        """Get generation level (log2 of sosa number)."""
        if self.value <= 0:
            return 0
        # Fix: Generation should be based on distance from child (Sosa 1)
        # Lower generations have higher Sosa numbers
        gen = int(math.log2(self.value)) if self.value > 0 else 0
        return gen
    
    def is_father(self) -> bool:
        """Check if this Sosa number represents a father (even number)."""
        return self.value % 2 == 0
    
    def is_mother(self) -> bool:
        """Check if this Sosa number represents a mother (odd number > 1)."""
        return self.value % 2 == 1 and self.value > 1


@dataclass
class RelatedPerson:
    """Represents a related person with relationship type."""
    person_id: int
    relation_type: RelationType
    source: str = ""


@dataclass 
class Person:
    """Represents a person in the genealogy database."""
    id: int
    name: Name
    sex: Sex = Sex.NEUTER
    birth: Optional[Event] = None
    death: Optional[Event] = None
    burial: Optional[Event] = None
    baptism: Optional[Event] = None
    events: List[Event] = field(default_factory=list)
    titles: List[Title] = field(default_factory=list)
    
    # Family relationships  
    parents: Optional[int] = None  # Family ID where this person is a child
    families: List[int] = field(default_factory=list)  # Family IDs where this person is a spouse
    related: List[RelatedPerson] = field(default_factory=list)  # Non-biological relations
    
    # Additional info
    occupation: str = ""
    public_name: str = ""
    image: str = ""
    notes: str = ""
    psources: str = ""
    
    # Birth/death details
    birth_place: str = ""
    birth_note: str = ""
    birth_src: str = ""
    death_place: str = ""
    death_note: str = ""
    death_src: str = ""
    burial_place: str = ""
    burial_note: str = ""
    burial_src: str = ""
    baptism_place: str = ""
    baptism_note: str = ""
    baptism_src: str = ""
    
    # Consanguinity  
    consang: float = 0.0
    
    # Access control
    access: Access = Access.IFTITLES
    
    # Sosa numbering (for ancestor trees)
    sosa: Optional[SosaNumber] = None
    
    # Key for disambiguation (first_name.occ surname)
    key_index: Optional[int] = None
    
    def __str__(self) -> str:
        """String representation of the person."""
        return f"{self.name.first_name} {self.name.surname}"
    
    def full_name(self) -> str:
        """Get full name including public name if available."""
        if self.public_name:
            return self.public_name
        return f"{self.name.first_name} {self.name.surname}"
    
    def designation(self) -> str:
        """Get designation (first_name.occ surname) for unique identification."""
        return f"{self.name.first_name}.{self.name.occ} {self.name.surname}"


class MarriageType(Enum):
    """Types of marriage/union."""
    MARRIED = "married"
    NOT_MARRIED = "not_married"
    ENGAGED = "engaged"
    NO_SEXES_CHECK = "no_sexes_check"
    NO_MENTION = "no_mention"
    NO_WEDDING = "no_wedding"


class DivorceType(Enum):
    """Types of divorce/separation."""
    NOT_DIVORCED = "not_divorced"
    DIVORCED = "divorced"
    SEPARATED = "separated"


class FamilyEventType(Enum):
    """Types of family events."""
    MARRIAGE = "marriage"
    NO_MARRIAGE = "no_marriage"
    NO_MENTION = "no_mention"
    ENGAGE = "engage"
    DIVORCE = "divorce"
    SEPARATED = "separated"
    ANNULATION = "annulation"
    MARRIAGE_BANN = "marriage_bann"
    MARRIAGE_CONTRACT = "marriage_contract"
    MARRIAGE_LICENSE = "marriage_license"
    PACS = "pacs"
    RESIDENCE = "residence"


@dataclass
class FamilyEvent:
    """Represents a family event."""
    event_type: FamilyEventType
    date: Optional[Date] = None
    place: Optional[Place] = None
    reason: str = ""
    note: str = ""
    source: str = ""
    witnesses: List[int] = field(default_factory=list)  # Person IDs


@dataclass
class Family:
    """Represents a family unit (parents and children)."""
    id: int
    father: Optional[int] = None  # Person ID
    mother: Optional[int] = None  # Person ID
    children: List[int] = field(default_factory=list)  # Person IDs
    
    # Marriage/union information
    marriage: MarriageType = MarriageType.MARRIED
    marriage_date: Optional[Date] = None
    marriage_place: Optional[Place] = None
    marriage_note: str = ""
    marriage_source: str = ""
    
    # Divorce information
    divorce: DivorceType = DivorceType.NOT_DIVORCED
    divorce_date: Optional[Date] = None
    
    # Events
    events: List[FamilyEvent] = field(default_factory=list)
    
    # Additional info
    notes: str = ""
    fsources: str = ""
    
    def __str__(self) -> str:
        """String representation of the family."""
        return f"Family {self.id} (Father: {self.father}, Mother: {self.mother})"


@dataclass
class Database:
    """Represents the entire genealogy database."""
    persons: Dict[int, Person] = field(default_factory=dict)
    families: Dict[int, Family] = field(default_factory=dict)
    
    # Indexing structures
    name_index: Dict[str, List[int]] = field(default_factory=dict)  # surname -> person_ids
    first_name_index: Dict[str, List[int]] = field(default_factory=dict)  # first_name -> person_ids
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    
    def add_person(self, person: Person) -> None:
        """Add a person to the database."""
        self.persons[person.id] = person
        self._update_indexes(person)
        self.modified_date = datetime.now()
    
    def add_family(self, family: Family) -> None:
        """Add a family to the database."""
        self.families[family.id] = family
        self.modified_date = datetime.now()
    
    def _update_indexes(self, person: Person) -> None:
        """Update name indexes when adding a person."""
        # Update surname index
        surname = person.name.surname.lower()
        if surname:
            if surname not in self.name_index:
                self.name_index[surname] = []
            if person.id not in self.name_index[surname]:
                self.name_index[surname].append(person.id)
        
        # Update first name index
        first_name = person.name.first_name.lower()
        if first_name:
            if first_name not in self.first_name_index:
                self.first_name_index[first_name] = []
            if person.id not in self.first_name_index[first_name]:
                self.first_name_index[first_name].append(person.id)
    
    def find_persons_by_surname(self, surname: str) -> List[Person]:
        """Find all persons with a given surname."""
        person_ids = self.name_index.get(surname.lower(), [])
        return [self.persons[pid] for pid in person_ids if pid in self.persons]
    
    def find_persons_by_first_name(self, first_name: str) -> List[Person]:
        """Find all persons with a given first name."""
        person_ids = self.first_name_index.get(first_name.lower(), [])
        return [self.persons[pid] for pid in person_ids if pid in self.persons]
    
    def get_person_parents(self, person_id: int) -> Optional[Family]:
        """Get the family where the person is a child."""
        person = self.persons.get(person_id)
        if person and person.parents:
            return self.families.get(person.parents)
        return None
    
    def get_person_children(self, person_id: int) -> List[Person]:
        """Get all children of a person."""
        children = []
        for family in self.families.values():
            if family.father == person_id or family.mother == person_id:
                for child_id in family.children:
                    if child_id in self.persons:
                        children.append(self.persons[child_id])
        return children
    
    def stats(self) -> Dict[str, int]:
        """Get database statistics."""
        return {
            "persons": len(self.persons),
            "families": len(self.families),
            "males": len([p for p in self.persons.values() if p.sex == Sex.MALE]),
            "females": len([p for p in self.persons.values() if p.sex == Sex.FEMALE]),
            "unknown_sex": len([p for p in self.persons.values() if p.sex == Sex.NEUTER])
        }


# Pydantic models for API serialization
class PersonAPI(BaseModel):
    """Pydantic model for Person API serialization."""
    id: int
    first_name: str = Field(alias="name.first_name")
    surname: str = Field(alias="name.surname")
    sex: Sex
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    occupation: str = ""
    
    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class FamilyAPI(BaseModel):
    """Pydantic model for Family API serialization."""
    id: int
    father_id: Optional[int] = Field(alias="father")
    mother_id: Optional[int] = Field(alias="mother")
    children_ids: List[int] = Field(alias="children")
    marriage_type: MarriageType = Field(alias="marriage")
    marriage_date: Optional[str] = None
    
    class Config:
        use_enum_values = True
        allow_population_by_field_name = True