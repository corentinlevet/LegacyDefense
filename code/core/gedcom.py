"""
GEDCOM parser for GeneWeb Python implementation.

This module handles importing genealogy data from GEDCOM files,
converting them to the GeneWeb data model.
"""
import re
from typing import Dict, List, Optional, Tuple, Any, Iterator
from datetime import datetime
from dataclasses import dataclass

from .models import (
    Person, Family, Event, Date, Place, Name, Title,
    Sex, EventType, DatePrecision, Calendar, MarriageType, DivorceType
)


@dataclass
class GedcomRecord:
    """Represents a single GEDCOM record."""
    level: int
    tag: str
    value: str
    xref_id: Optional[str] = None
    children: List['GedcomRecord'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def find_child(self, tag: str) -> Optional['GedcomRecord']:
        """Find first child with given tag."""
        for child in self.children:
            if child.tag == tag:
                return child
        return None
    
    def find_children(self, tag: str) -> List['GedcomRecord']:
        """Find all children with given tag."""
        return [child for child in self.children if child.tag == tag]
    
    def get_value(self, tag: str, default: str = "") -> str:
        """Get value of first child with given tag."""
        child = self.find_child(tag)
        return child.value if child else default


class GedcomParser:
    """GEDCOM file parser."""
    
    def __init__(self):
        self.persons: Dict[str, Person] = {}
        self.families: Dict[str, Family] = {}
        self.person_id_counter = 1
        self.family_id_counter = 1
        self.xref_to_person_id: Dict[str, int] = {}
        self.xref_to_family_id: Dict[str, int] = {}
    
    def parse_file(self, file_path: str) -> Tuple[Dict[int, Person], Dict[int, Family]]:
        """Parse a GEDCOM file and return persons and families."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse GEDCOM records
        records = self._parse_gedcom_content(content)
        
        # Process records
        for record in records:
            if record.tag == "INDI":
                self._process_individual(record)
            elif record.tag == "FAM":
                self._process_family(record)
        
        # Convert to final format
        persons = {self.xref_to_person_id[xref]: person 
                  for xref, person in self.persons.items()}
        families = {self.xref_to_family_id[xref]: family 
                   for xref, family in self.families.items()}
        
        return persons, families
    
    def _parse_gedcom_content(self, content: str) -> List[GedcomRecord]:
        """Parse GEDCOM content into structured records."""
        lines = content.strip().split('\n')
        root_records = []
        stack = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse GEDCOM line format: level [xref_id] tag [value]
            match = re.match(r'^(\d+)\s+(@[^@]+@\s+)?(\w+)(\s+(.*))?$', line)
            if not match:
                continue
            
            level = int(match.group(1))
            xref_id = match.group(2).strip() if match.group(2) else None
            tag = match.group(3)
            value = match.group(5) if match.group(5) else ""
            
            # Clean xref_id
            if xref_id:
                xref_id = xref_id.strip("@ ")
            
            record = GedcomRecord(level=level, tag=tag, value=value, xref_id=xref_id)
            
            # Build hierarchy
            if level == 0:
                root_records.append(record)
                stack = [record]
            else:
                # Find parent at correct level
                while len(stack) > level:
                    stack.pop()
                
                if stack:
                    parent = stack[-1]
                    parent.children.append(record)
                
                stack.append(record)
        
        return root_records
    
    def _process_individual(self, record: GedcomRecord) -> None:
        """Process an individual (INDI) record."""
        if not record.xref_id:
            return
        
        person_id = self.person_id_counter
        self.person_id_counter += 1
        self.xref_to_person_id[record.xref_id] = person_id
        
        # Parse name
        name = self._parse_name(record)
        
        # Parse sex
        sex = self._parse_sex(record)
        
        # Parse events
        birth = self._parse_birth(record)
        death = self._parse_death(record)
        burial = self._parse_burial(record)
        events = self._parse_events(record)
        
        # Parse additional info
        occupation = record.get_value("OCCU")
        notes = self._parse_notes(record)
        
        person = Person(
            id=person_id,
            name=name,
            sex=sex,
            birth=birth,
            death=death,
            burial=burial,
            events=events,
            occupation=occupation,
            notes=notes
        )
        
        self.persons[record.xref_id] = person
    
    def _process_family(self, record: GedcomRecord) -> None:
        """Process a family (FAM) record."""
        if not record.xref_id:
            return
        
        family_id = self.family_id_counter
        self.family_id_counter += 1
        self.xref_to_family_id[record.xref_id] = family_id
        
        # Parse parents
        father_xref = None
        mother_xref = None
        
        husb = record.find_child("HUSB")
        if husb:
            father_xref = husb.value.strip("@")
        
        wife = record.find_child("WIFE")
        if wife:
            mother_xref = wife.value.strip("@")
        
        # Parse children
        children_xrefs = []
        for child_record in record.find_children("CHIL"):
            children_xrefs.append(child_record.value.strip("@"))
        
        # Parse marriage info
        marriage_type = MarriageType.MARRIED
        marriage_date = None
        marriage_place = None
        
        marr = record.find_child("MARR")
        if marr:
            marriage_date = self._parse_date(marr.find_child("DATE"))
            marriage_place = self._parse_place(marr.find_child("PLAC"))
        
        # Parse divorce info
        divorce_type = DivorceType.NOT_DIVORCED
        divorce_date = None
        
        div = record.find_child("DIV")
        if div:
            divorce_type = DivorceType.DIVORCED
            divorce_date = self._parse_date(div.find_child("DATE"))
        
        family = Family(
            id=family_id,
            marriage=marriage_type,
            marriage_date=marriage_date,
            marriage_place=marriage_place,
            divorce=divorce_type,
            divorce_date=divorce_date
        )
        
        self.families[record.xref_id] = family
        
        # Store relationships for later linking
        family._father_xref = father_xref
        family._mother_xref = mother_xref
        family._children_xrefs = children_xrefs
    
    def _parse_name(self, record: GedcomRecord) -> Name:
        """Parse name from individual record."""
        name = Name()
        
        name_record = record.find_child("NAME")
        if name_record:
            name_value = name_record.value
            
            # Parse name format: "Given names /Surname/"
            match = re.match(r'^([^/]*?)(?:/([^/]*)/)?(.*)$', name_value)
            if match:
                given_names = match.group(1).strip()
                surname = match.group(2) if match.group(2) else ""
                suffix = match.group(3).strip()
                
                name.first_name = given_names
                name.surname = surname
                
                # Parse additional name components
                givn = name_record.find_child("GIVN")
                if givn:
                    name.first_name = givn.value
                
                surn = name_record.find_child("SURN")
                if surn:
                    name.surname = surn.value
        
        return name
    
    def _parse_sex(self, record: GedcomRecord) -> Sex:
        """Parse sex from individual record."""
        sex_record = record.find_child("SEX")
        if sex_record:
            sex_value = sex_record.value.upper()
            if sex_value == "M":
                return Sex.MALE
            elif sex_value == "F":
                return Sex.FEMALE
        return Sex.NEUTER
    
    def _parse_birth(self, record: GedcomRecord) -> Optional[Event]:
        """Parse birth event from individual record."""
        birth_record = record.find_child("BIRT")
        if birth_record:
            return Event(
                event_type=EventType.BIRTH,
                date=self._parse_date(birth_record.find_child("DATE")),
                place=self._parse_place(birth_record.find_child("PLAC")),
                note=birth_record.get_value("NOTE")
            )
        return None
    
    def _parse_death(self, record: GedcomRecord) -> Optional[Event]:
        """Parse death event from individual record."""
        death_record = record.find_child("DEAT")
        if death_record:
            return Event(
                event_type=EventType.DEATH,
                date=self._parse_date(death_record.find_child("DATE")),
                place=self._parse_place(death_record.find_child("PLAC")),
                note=death_record.get_value("NOTE")
            )
        return None
    
    def _parse_burial(self, record: GedcomRecord) -> Optional[Event]:
        """Parse burial event from individual record."""
        burial_record = record.find_child("BURI")
        if burial_record:
            return Event(
                event_type=EventType.BURIAL,
                date=self._parse_date(burial_record.find_child("DATE")),
                place=self._parse_place(burial_record.find_child("PLAC")),
                note=burial_record.get_value("NOTE")
            )
        return None
    
    def _parse_events(self, record: GedcomRecord) -> List[Event]:
        """Parse other events from individual record."""
        events = []
        
        # Map GEDCOM tags to EventType
        event_mapping = {
            "BAPM": EventType.BAPTISM,
            "CHR": EventType.BAPTISM,
            "CONF": EventType.CONFIRMATION,
            "GRAD": EventType.GRADUATE,
            "OCCU": EventType.OCCUPATION,
            "RESI": EventType.RESIDENCE,
            "RETI": EventType.RETIRED,
            "WILL": EventType.WILL,
            "EMIG": EventType.EMIGRATION,
            "IMMI": EventType.IMMIGRATION,
            "NATU": EventType.NATURALISATION,
            "CENS": EventType.RECENSEMENT,
        }
        
        for tag, event_type in event_mapping.items():
            for event_record in record.find_children(tag):
                event = Event(
                    event_type=event_type,
                    date=self._parse_date(event_record.find_child("DATE")),
                    place=self._parse_place(event_record.find_child("PLAC")),
                    note=event_record.get_value("NOTE")
                )
                events.append(event)
        
        return events
    
    def _parse_date(self, date_record: Optional[GedcomRecord]) -> Optional[Date]:
        """Parse date from GEDCOM date record."""
        if not date_record or not date_record.value:
            return None
        
        date_str = date_record.value.strip()
        if not date_str:
            return None
        
        # Parse date patterns
        date = Date()
        
        # Handle date modifiers
        if date_str.startswith("ABT "):
            date.precision = DatePrecision.ABOUT
            date_str = date_str[4:]
        elif date_str.startswith("BEF "):
            date.precision = DatePrecision.BEFORE
            date_str = date_str[4:]
        elif date_str.startswith("AFT "):
            date.precision = DatePrecision.AFTER
            date_str = date_str[4:]
        elif date_str.startswith("EST "):
            date.precision = DatePrecision.ABOUT
            date_str = date_str[4:]
        
        # Parse date components
        date_parts = date_str.split()
        
        if len(date_parts) >= 1:
            # Try to parse year
            year_str = date_parts[-1]
            try:
                date.year = int(year_str)
            except ValueError:
                pass
        
        if len(date_parts) >= 2:
            # Try to parse month
            month_str = date_parts[-2].upper()
            months = {
                "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
                "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
            }
            if month_str in months:
                date.month = months[month_str]
        
        if len(date_parts) >= 3:
            # Try to parse day
            day_str = date_parts[-3]
            try:
                date.day = int(day_str)
            except ValueError:
                pass
        
        return date
    
    def _parse_place(self, place_record: Optional[GedcomRecord]) -> Optional[Place]:
        """Parse place from GEDCOM place record."""
        if not place_record or not place_record.value:
            return None
        
        place_str = place_record.value.strip()
        if not place_str:
            return None
        
        # Split place components (usually comma-separated)
        components = [p.strip() for p in place_str.split(",")]
        
        place = Place()
        
        # Assign components based on position (most specific to least specific)
        if len(components) >= 1:
            place.place = components[0]
        if len(components) >= 2:
            place.town = components[1]
        if len(components) >= 3:
            place.county = components[2]
        if len(components) >= 4:
            place.state = components[3]
        if len(components) >= 5:
            place.country = components[4]
        
        return place
    
    def _parse_notes(self, record: GedcomRecord) -> str:
        """Parse notes from record."""
        notes = []
        for note_record in record.find_children("NOTE"):
            notes.append(note_record.value)
        return " ".join(notes)
    
    def link_families(self) -> None:
        """Link family relationships after all records are processed."""
        # Link father/mother to families
        for family_xref, family in self.families.items():
            if hasattr(family, '_father_xref') and family._father_xref:
                if family._father_xref in self.xref_to_person_id:
                    family.father = self.xref_to_person_id[family._father_xref]
                    person = self.persons[family._father_xref]
                    person.families.append(self.xref_to_family_id[family_xref])
            
            if hasattr(family, '_mother_xref') and family._mother_xref:
                if family._mother_xref in self.xref_to_person_id:
                    family.mother = self.xref_to_person_id[family._mother_xref]
                    person = self.persons[family._mother_xref]
                    person.families.append(self.xref_to_family_id[family_xref])
            
            # Link children to family
            if hasattr(family, '_children_xrefs'):
                for child_xref in family._children_xrefs:
                    if child_xref in self.xref_to_person_id:
                        child_id = self.xref_to_person_id[child_xref]
                        family.children.append(child_id)
                        child = self.persons[child_xref]
                        child.parents = self.xref_to_family_id[family_xref]


class GedcomExporter:
    """Export GeneWeb data to GEDCOM format."""
    
    def __init__(self, persons: Dict[int, Person], families: Dict[int, Family]):
        self.persons = persons
        self.families = families
        self.person_to_xref: Dict[int, str] = {}
        self.family_to_xref: Dict[int, str] = {}
        
        # Generate XREF IDs
        for person_id in persons:
            self.person_to_xref[person_id] = f"I{person_id}"
        for family_id in families:
            self.family_to_xref[family_id] = f"F{family_id}"
    
    def export_to_file(self, file_path: str) -> None:
        """Export to GEDCOM file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            self._write_header(f)
            self._write_individuals(f)
            self._write_families(f)
            self._write_trailer(f)
    
    def _write_header(self, f) -> None:
        """Write GEDCOM header."""
        f.write("0 HEAD\n")
        f.write("1 SOUR GENEWEB\n")
        f.write("2 NAME GeneWeb Python\n")
        f.write("2 VERS 1.0\n")
        f.write("1 DEST ANY\n")
        f.write("1 DATE " + datetime.now().strftime("%d %b %Y") + "\n")
        f.write("1 CHAR UTF-8\n")
        f.write("1 GEDC\n")
        f.write("2 VERS 5.5.1\n")
        f.write("2 FORM LINEAGE-LINKED\n")
    
    def _write_individuals(self, f) -> None:
        """Write individual records."""
        for person_id, person in self.persons.items():
            xref = self.person_to_xref[person_id]
            f.write(f"0 @{xref}@ INDI\n")
            
            # Name
            name_value = f"{person.name.first_name} /{person.name.surname}/"
            f.write(f"1 NAME {name_value}\n")
            if person.name.first_name:
                f.write(f"2 GIVN {person.name.first_name}\n")
            if person.name.surname:
                f.write(f"2 SURN {person.name.surname}\n")
            
            # Sex
            if person.sex == Sex.MALE:
                f.write("1 SEX M\n")
            elif person.sex == Sex.FEMALE:
                f.write("1 SEX F\n")
            
            # Birth
            if person.birth:
                f.write("1 BIRT\n")
                self._write_event(f, person.birth, 2)
            
            # Death
            if person.death:
                f.write("1 DEAT\n")
                self._write_event(f, person.death, 2)
            
            # Burial
            if person.burial:
                f.write("1 BURI\n")
                self._write_event(f, person.burial, 2)
            
            # Family relationships
            if person.parents:
                family_xref = self.family_to_xref.get(person.parents)
                if family_xref:
                    f.write(f"1 FAMC @{family_xref}@\n")
            
            for family_id in person.families:
                family_xref = self.family_to_xref.get(family_id)
                if family_xref:
                    f.write(f"1 FAMS @{family_xref}@\n")
            
            # Notes
            if person.notes:
                f.write(f"1 NOTE {person.notes}\n")
    
    def _write_families(self, f) -> None:
        """Write family records."""
        for family_id, family in self.families.items():
            xref = self.family_to_xref[family_id]
            f.write(f"0 @{xref}@ FAM\n")
            
            # Father
            if family.father:
                father_xref = self.person_to_xref.get(family.father)
                if father_xref:
                    f.write(f"1 HUSB @{father_xref}@\n")
            
            # Mother
            if family.mother:
                mother_xref = self.person_to_xref.get(family.mother)
                if mother_xref:
                    f.write(f"1 WIFE @{mother_xref}@\n")
            
            # Children
            for child_id in family.children:
                child_xref = self.person_to_xref.get(child_id)
                if child_xref:
                    f.write(f"1 CHIL @{child_xref}@\n")
            
            # Marriage
            if family.marriage_date or family.marriage_place:
                f.write("1 MARR\n")
                if family.marriage_date:
                    f.write(f"2 DATE {self._format_date(family.marriage_date)}\n")
                if family.marriage_place:
                    f.write(f"2 PLAC {self._format_place(family.marriage_place)}\n")
            
            # Divorce
            if family.divorce_date:
                f.write("1 DIV\n")
                f.write(f"2 DATE {self._format_date(family.divorce_date)}\n")
    
    def _write_event(self, f, event: Event, level: int) -> None:
        """Write event information."""
        if event.date:
            f.write(f"{level} DATE {self._format_date(event.date)}\n")
        if event.place:
            f.write(f"{level} PLAC {self._format_place(event.place)}\n")
        if event.note:
            f.write(f"{level} NOTE {event.note}\n")
    
    def _format_date(self, date: Date) -> str:
        """Format date for GEDCOM output."""
        date_parts = []
        
        if date.day:
            date_parts.append(f"{date.day:02d}")
        
        if date.month:
            months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                     "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            date_parts.append(months[date.month - 1])
        
        if date.year:
            date_parts.append(str(date.year))
        
        date_str = " ".join(date_parts)
        
        # Add precision modifier
        if date.precision == DatePrecision.ABOUT:
            date_str = f"ABT {date_str}"
        elif date.precision == DatePrecision.BEFORE:
            date_str = f"BEF {date_str}"
        elif date.precision == DatePrecision.AFTER:
            date_str = f"AFT {date_str}"
        
        return date_str
    
    def _format_place(self, place: Place) -> str:
        """Format place for GEDCOM output."""
        components = []
        for component in [place.place, place.town, place.county, place.state, place.country]:
            if component:
                components.append(component)
        return ", ".join(components)
    
    def _write_trailer(self, f) -> None:
        """Write GEDCOM trailer."""
        f.write("0 TRLR\n")