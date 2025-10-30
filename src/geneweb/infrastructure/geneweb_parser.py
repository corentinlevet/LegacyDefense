"""
Parser for GeneWeb (.gw) file format.
This module converts GeneWeb files to GEDCOM format for import and vice versa.
"""

import re
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from .models import Family, Person


class GeneWebParser:
    """Parser for GeneWeb file format."""

    def __init__(self):
        self.persons: Dict[str, Dict] = {}
        self.families: List[Dict] = []
        self.person_counter = 0
        self.family_counter = 0

    def import_to_db(self, content: str, genealogy_id: int, db: "Session"):
        """
        Parse GeneWeb content and import directly to database.

        Args:
            content: The content of the .gw file
            genealogy_id: The ID of the genealogy to import into
            db: SQLAlchemy database session
        """
        from .models import Family, Person

        # First parse the content to build internal structures
        lines = content.split("\n")
        current_section = None
        current_family = None
        current_person_key = None
        buffer = []

        for line in lines:
            line = line.rstrip()

            # Skip encoding and gwplus lines
            if line.startswith("encoding:") or line == "gwplus":
                continue

            # Family definition
            if line.startswith("fam "):
                if current_family:
                    self._process_family(current_family, buffer)
                current_family = self._parse_family_line(line)
                current_section = "family"
                buffer = []
                continue

            # Family events
            if line == "fevt":
                current_section = "fevt"
                buffer = []
                continue

            # Children section
            if line == "beg":
                current_section = "children"
                buffer = []
                continue

            # Person events
            if line.startswith("pevt "):
                current_section = "pevt"
                current_person_key = self._extract_person_key(line)
                buffer = []
                continue

            # Notes section
            if line.startswith("notes "):
                current_section = "notes"
                current_person_key = self._extract_person_key(line)
                buffer = []
                continue

            # End of section
            if (
                line == "end"
                or line == "end pevt"
                or line == "end fevt"
                or line == "end notes"
            ):
                if current_section == "fevt" and current_family:
                    current_family["events"] = buffer
                elif current_section == "children" and current_family:
                    current_family["children"] = buffer
                elif current_section == "pevt" and current_person_key:
                    self._add_person_events(current_person_key, buffer)
                elif current_section == "notes" and current_person_key:
                    self._add_person_notes(current_person_key, buffer)
                buffer = []
                current_section = None
                continue

            # Collect lines in buffer
            if current_section:
                buffer.append(line)

        # Process last family if exists
        if current_family:
            self._process_family(current_family, [])

        # Now import to database
        person_db_map = {}  # Map from person_key to DB Person object

        # Create all persons first
        for person_key, person_data in self.persons.items():
            person_obj = Person(
                genealogy_id=genealogy_id,
                first_name=person_data["firstname"],
                surname=person_data["surname"],
                sex=person_data["attrs"].get("sex", "U"),
                birth_date=self._convert_date_to_db(
                    person_data["attrs"].get("birth_date")
                    or person_data["attrs"].get("date")
                ),
                occupation=(
                    person_data["attrs"].get("occu", "").replace("_", " ")
                    if "occu" in person_data["attrs"]
                    else None
                ),
            )

            # Handle death
            if person_data["attrs"].get("death") == "od":
                person_obj.death_date = "Deceased"

            # Process person events
            for event_line in person_data.get("events", []):
                if event_line.startswith("#birt"):
                    parts = event_line.split()
                    if len(parts) > 1:
                        person_obj.birth_date = self._convert_date_to_db(parts[1])
                    # Look for place
                    for i, part in enumerate(parts):
                        if part == "#p" and i + 1 < len(parts):
                            person_obj.birth_place = " ".join(parts[i + 1 :]).replace(
                                "_", " "
                            )
                            break

                elif event_line.startswith("#deat"):
                    parts = event_line.split()
                    if len(parts) > 1:
                        person_obj.death_date = self._convert_date_to_db(parts[1])
                    # Look for place
                    for i, part in enumerate(parts):
                        if part == "#p" and i + 1 < len(parts):
                            person_obj.death_place = " ".join(parts[i + 1 :]).replace(
                                "_", " "
                            )
                            break

            # Notes
            if person_data.get("notes"):
                person_obj.notes = "\n".join(person_data["notes"])

            db.add(person_obj)
            person_db_map[person_key] = person_obj

        db.flush()  # Assign IDs to persons

        # Create families
        for family_data in self.families:
            husband = family_data.get("husband")
            wife = family_data.get("wife")

            # Get husband and wife IDs safely
            husband_id = None
            wife_id = None

            if husband:
                husband_key = f"{husband['surname']} {husband['firstname']}"
                if husband_key in person_db_map:
                    husband_id = person_db_map[husband_key].id

            if wife:
                wife_key = f"{wife['surname']} {wife['firstname']}"
                if wife_key in person_db_map:
                    wife_id = person_db_map[wife_key].id

            family_obj = Family(
                genealogy_id=genealogy_id,
                father_id=husband_id,
                mother_id=wife_id,
            )

            # Process family events
            for event_line in family_data.get("events", []):
                if event_line.startswith("#marr"):
                    parts = event_line.split()
                    if len(parts) > 1:
                        family_obj.marriage_date = self._convert_date_to_db(parts[1])

            db.add(family_obj)
            db.flush()  # Get family ID

            # Add children
            for child in family_data.get("children", []):
                # Child is already a person object from self.persons
                child_key = f"{child['surname']} {child['firstname']}"
                if child_key in person_db_map:
                    family_obj.children.append(person_db_map[child_key])

    def _convert_date_to_db(self, date_str: str) -> Optional[str]:
        """Convert GeneWeb date format to database format."""
        if not date_str:
            return None

        # Handle special prefixes
        if date_str.startswith("<"):
            return f"Avant {date_str[1:]}"
        if date_str.startswith(">"):
            return f"Après {date_str[1:]}"

        # Try to parse DD/MM/YYYY format
        if "/" in date_str:
            try:
                parts = date_str.split("/")
                if len(parts) == 3:
                    day, month, year = parts
                    months = [
                        "janvier",
                        "février",
                        "mars",
                        "avril",
                        "mai",
                        "juin",
                        "juillet",
                        "août",
                        "septembre",
                        "octobre",
                        "novembre",
                        "décembre",
                    ]
                    month_name = (
                        months[int(month) - 1] if 1 <= int(month) <= 12 else month
                    )
                    return f"{day} {month_name} {year}"
            except:
                pass

        return date_str

    def parse(self, content: str) -> str:
        """
        Parse GeneWeb content and convert to GEDCOM format.

        Args:
            content: The content of the .gw file

        Returns:
            GEDCOM formatted string
        """
        lines = content.split("\n")
        current_section = None
        current_family = None
        current_person_key = None
        buffer = []

        for line in lines:
            line = line.rstrip()

            # Skip encoding and gwplus lines
            if line.startswith("encoding:") or line == "gwplus":
                continue

            # Family definition
            if line.startswith("fam "):
                if current_family:
                    self._process_family(current_family, buffer)
                current_family = self._parse_family_line(line)
                current_section = "family"
                buffer = []
                continue

            # Family events
            if line == "fevt":
                current_section = "fevt"
                buffer = []
                continue

            # Children section
            if line == "beg":
                current_section = "children"
                buffer = []
                continue

            # Person events
            if line.startswith("pevt "):
                current_section = "pevt"
                current_person_key = self._extract_person_key(line)
                buffer = []
                continue

            # Notes section
            if line.startswith("notes "):
                current_section = "notes"
                current_person_key = self._extract_person_key(line)
                buffer = []
                continue

            # End of section
            if (
                line == "end"
                or line == "end pevt"
                or line == "end fevt"
                or line == "end notes"
            ):
                if current_section == "family" and current_family:
                    pass  # Already processed
                elif current_section == "fevt" and current_family:
                    current_family["events"] = buffer
                elif current_section == "children" and current_family:
                    current_family["children"] = buffer
                elif current_section == "pevt" and current_person_key:
                    self._add_person_events(current_person_key, buffer)
                elif current_section == "notes" and current_person_key:
                    self._add_person_notes(current_person_key, buffer)
                buffer = []
                current_section = None
                continue

            # Collect lines in buffer
            if current_section:
                buffer.append(line)

        # Process last family if exists
        if current_family:
            self._process_family(current_family, [])

        # Generate GEDCOM
        return self._generate_gedcom()

    def _parse_family_line(self, line: str) -> Dict:
        """Parse a family definition line."""
        # Format: fam SURNAME FirstName #attrs... 0 date + SURNAME2 FirstName2 #attrs... 0 date
        parts = line[4:].strip()  # Remove 'fam '

        # Split by ' + ' to separate husband and wife
        if " + " in parts:
            husband_part, wife_part = parts.split(" + ", 1)
        else:
            husband_part = parts
            wife_part = None

        husband = self._parse_person_part(husband_part)
        wife = self._parse_person_part(wife_part) if wife_part else None

        return {"husband": husband, "wife": wife, "children": [], "events": []}

    def _parse_person_part(self, part: str) -> Optional[Dict]:
        """Parse a person definition from family line."""
        if not part or part.strip() == "":
            return None

        tokens = part.strip().split()
        if len(tokens) < 2:
            return None

        surname = tokens[0]
        firstname = tokens[1]

        # Parse additional attributes
        attrs = {}
        i = 2
        while i < len(tokens):
            token = tokens[i]
            if token.startswith("#"):
                attr_name = token[1:]
                attr_value = []
                i += 1
                while (
                    i < len(tokens)
                    and not tokens[i].startswith("#")
                    and tokens[i] not in ["0", "+"]
                ):
                    attr_value.append(tokens[i])
                    i += 1
                attrs[attr_name] = " ".join(attr_value)
            elif token in ["0", "+"]:
                i += 1
            elif re.match(r"[<>]?\d+", token) or "/" in token:
                # Date
                attrs["date"] = token
                i += 1
            else:
                i += 1

        person_key = f"{surname} {firstname}"
        if person_key not in self.persons:
            self.person_counter += 1
            self.persons[person_key] = {
                "id": f"@I{self.person_counter}@",
                "surname": surname,
                "firstname": firstname.replace("_", " "),
                "attrs": attrs,
                "events": [],
                "notes": [],
            }

        return self.persons[person_key]

    def _parse_child_line(self, line: str) -> Optional[Dict]:
        """Parse a child line from the children section."""
        # Format: - h/f FirstName #attrs... date
        if not line.startswith("-"):
            return None

        parts = line[1:].strip().split()
        if len(parts) < 2:
            return None

        sex = "M" if parts[0] == "h" else "F"
        firstname = parts[1]

        attrs = {"sex": sex}
        i = 2
        while i < len(parts):
            token = parts[i]
            if token.startswith("#"):
                attr_name = token[1:]
                attr_value = []
                i += 1
                while i < len(parts) and not parts[i].startswith("#"):
                    attr_value.append(parts[i])
                    i += 1
                attrs[attr_name] = " ".join(attr_value)
            elif re.match(r"\d+/\d+/\d+", token) or re.match(r"[<>]?\d+", token):
                attrs["birth_date"] = token
                i += 1
            elif token == "od":
                attrs["death"] = "od"  # Deceased
                i += 1
            else:
                i += 1

        return {"firstname": firstname.replace("_", " "), "attrs": attrs}

    def _extract_person_key(self, line: str) -> str:
        """Extract person key from 'pevt' or 'notes' line."""
        # Format: pevt SURNAME FirstName or notes SURNAME FirstName
        parts = line.split()[1:]
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1]}"
        return ""

    def _add_person_events(self, person_key: str, events: List[str]):
        """Add events to a person."""
        if person_key in self.persons:
            self.persons[person_key]["events"] = events

    def _add_person_notes(self, person_key: str, notes: List[str]):
        """Add notes to a person."""
        if person_key in self.persons:
            self.persons[person_key]["notes"] = notes

    def _process_family(self, family: Dict, children_buffer: List[str]):
        """Process a complete family."""
        self.family_counter += 1
        family_id = f"@F{self.family_counter}@"

        # Parse children
        children = []
        for child_line in family.get("children", []):
            child = self._parse_child_line(child_line)
            if child:
                # Create child person based on parents' surname
                surname = (
                    family["husband"]["surname"]
                    if family.get("husband")
                    else (
                        family["wife"]["surname"] if family.get("wife") else "Unknown"
                    )
                )
                person_key = f"{surname} {child['firstname']}"

                if person_key not in self.persons:
                    self.person_counter += 1
                    self.persons[person_key] = {
                        "id": f"@I{self.person_counter}@",
                        "surname": surname,
                        "firstname": child["firstname"],
                        "attrs": child.get("attrs", {}),
                        "events": [],
                        "notes": [],
                    }

                children.append(self.persons[person_key])

        self.families.append(
            {
                "id": family_id,
                "husband": family.get("husband"),
                "wife": family.get("wife"),
                "children": children,
                "events": family.get("events", []),
            }
        )

    def _generate_gedcom(self) -> str:
        """Generate GEDCOM output from parsed data."""
        lines = []

        # Header
        lines.append("0 HEAD")
        lines.append("1 SOUR GeneWeb Import")
        lines.append("1 GEDC")
        lines.append("2 VERS 5.5.1")
        lines.append("1 CHAR UTF-8")

        # Persons
        for person_key, person in self.persons.items():
            lines.append(f"0 {person['id']} INDI")
            lines.append(f"1 NAME {person['firstname']} /{person['surname']}/")
            lines.append(f"2 GIVN {person['firstname']}")
            lines.append(f"2 SURN {person['surname']}")

            # Sex
            sex = person["attrs"].get("sex", "U")
            if sex != "U":
                lines.append(f"1 SEX {sex}")

            # Birth from attrs or events
            birth_date = person["attrs"].get("birth_date") or person["attrs"].get(
                "date"
            )
            if birth_date:
                lines.append("1 BIRT")
                lines.append(f"2 DATE {self._convert_date(birth_date)}")

            # Process events
            for event_line in person.get("events", []):
                self._process_event_line(lines, event_line)

            # Occupation
            if "occu" in person["attrs"]:
                lines.append(f"1 OCCU {person['attrs']['occu'].replace('_', ' ')}")

            # Death
            if person["attrs"].get("death") == "od":
                lines.append("1 DEAT Y")

            # Notes
            if person.get("notes"):
                note_text = "\n".join(person["notes"]).replace("beg", "").strip()
                if note_text:
                    lines.append(f"1 NOTE {note_text}")

        # Families
        for family in self.families:
            lines.append(f"0 {family['id']} FAM")

            if family.get("husband"):
                lines.append(f"1 HUSB {family['husband']['id']}")

            if family.get("wife"):
                lines.append(f"1 WIFE {family['wife']['id']}")

            for child in family.get("children", []):
                lines.append(f"1 CHIL {child['id']}")

            # Marriage event
            for event_line in family.get("events", []):
                if event_line.startswith("#marr"):
                    lines.append("1 MARR")
                    parts = event_line.split()
                    if len(parts) > 1:
                        date = parts[1]
                        lines.append(f"2 DATE {self._convert_date(date)}")

        # Trailer
        lines.append("0 TRLR")

        return "\n".join(lines)

    def _process_event_line(self, lines: List[str], event_line: str):
        """Process a single event line and add to GEDCOM."""
        event_line = event_line.strip()

        if event_line.startswith("#birt"):
            parts = event_line.split()
            lines.append("1 BIRT")
            if len(parts) > 1:
                date = parts[1]
                lines.append(f"2 DATE {self._convert_date(date)}")

            # Check for place
            for i, part in enumerate(parts):
                if part.startswith("#p"):
                    place = " ".join(parts[i + 1 :])
                    lines.append(f"2 PLAC {place.replace('_', ' ')}")
                    break

        elif event_line.startswith("#deat"):
            parts = event_line.split()
            lines.append("1 DEAT")
            if len(parts) > 1:
                date = parts[1]
                lines.append(f"2 DATE {self._convert_date(date)}")

    def _convert_date(self, date_str: str) -> str:
        """Convert GeneWeb date format to GEDCOM date format."""
        if not date_str:
            return ""

        # Handle special prefixes
        if date_str.startswith("<"):
            return f"BEF {date_str[1:]}"
        if date_str.startswith(">"):
            return f"AFT {date_str[1:]}"

        # Try to parse DD/MM/YYYY format
        if "/" in date_str:
            try:
                parts = date_str.split("/")
                if len(parts) == 3:
                    day, month, year = parts
                    months = [
                        "JAN",
                        "FEB",
                        "MAR",
                        "APR",
                        "MAY",
                        "JUN",
                        "JUL",
                        "AUG",
                        "SEP",
                        "OCT",
                        "NOV",
                        "DEC",
                    ]
                    month_name = (
                        months[int(month) - 1] if 1 <= int(month) <= 12 else month
                    )
                    return f"{day} {month_name} {year}"
            except:
                pass

        return date_str


class GeneWebExporter:
    """Exporter to GeneWeb file format from database."""

    def __init__(self, db: "Session", genealogy_name: str):
        # Import here to avoid circular imports
        from .models import Event, Family, Genealogy, Person

        self.db = db
        self.genealogy_name = genealogy_name
        self.genealogy = None
        self.Genealogy = Genealogy
        self.Family = Family
        self.Person = Person
        self.Event = Event
        self.exported_persons = set()  # Track exported persons to avoid duplicates

    def export(self) -> str:
        """
        Export database to GeneWeb format.

        Returns:
            GeneWeb formatted string
        """
        # Get genealogy
        self.genealogy = (
            self.db.query(self.Genealogy)
            .filter(self.Genealogy.name == self.genealogy_name)
            .first()
        )

        if not self.genealogy:
            raise ValueError(f"Genealogy '{self.genealogy_name}' not found")

        lines = []
        lines.append("encoding: utf-8")
        lines.append("gwplus")
        lines.append("")

        # Get all families
        families = (
            self.db.query(self.Family)
            .filter(self.Family.genealogy_id == self.genealogy.id)
            .all()
        )

        for family in families:
            self._export_family(lines, family)
            lines.append("")

        return "\n".join(lines)

    def _export_family(self, lines: List[str], family: "Family"):
        """Export a single family."""
        # Build family line
        fam_line = "fam"

        # Father (husband)
        if family.father:
            fam_line += f" {self._format_person_inline(family.father)}"
        else:
            fam_line += " ? ?"

        fam_line += " 0 +"

        # Mother (wife)
        if family.mother:
            fam_line += f" {self._format_person_inline(family.mother)}"
        else:
            fam_line += " ? ?"

        fam_line += " 0"

        lines.append(fam_line)

        # Family events
        if family.marriage_date:
            lines.append("fevt")
            lines.append(f"#marr {self._convert_date_to_gw(family.marriage_date)}")
            lines.append("end fevt")

        # Children
        if family.children:
            lines.append("beg")
            for child in family.children:
                sex_code = "h" if child.sex == "M" else "f"
                child_line = f"- {sex_code} {child.first_name.replace(' ', '_')}"

                # Birth date
                if child.birth_date:
                    child_line += f" {self._convert_date_to_gw(child.birth_date)}"

                # Death indicator
                if child.death_date:
                    child_line += " od"

                lines.append(child_line)
            lines.append("end")

        # Person events for father
        if family.father and family.father.id not in self.exported_persons:
            self._export_person_events(lines, family.father)
            self.exported_persons.add(family.father.id)

        # Person events for mother
        if family.mother and family.mother.id not in self.exported_persons:
            self._export_person_events(lines, family.mother)
            self.exported_persons.add(family.mother.id)

        # Person events for children
        for child in family.children:
            if child.id not in self.exported_persons:
                self._export_person_events(lines, child)
                self.exported_persons.add(child.id)

    def _format_person_inline(self, person: "Person") -> str:
        """Format person for inline family definition."""
        result = f"{person.surname} {person.first_name.replace(' ', '_')}"

        if person.occupation:
            result += f" #occu {person.occupation.replace(' ', '_')}"

        return result

    def _export_person_events(self, lines: List[str], person: "Person"):
        """Export events for a person."""
        has_events = (
            person.birth_date
            or person.death_date
            or person.birth_place
            or person.death_place
        )

        if not has_events:
            # Check for other events
            events = (
                self.db.query(self.Event)
                .filter(self.Event.person_id == person.id)
                .all()
            )
            if not events:
                return

        lines.append(f"pevt {person.surname} {person.first_name.replace(' ', '_')}")

        if person.birth_date or person.birth_place:
            event_line = "#birt"
            if person.birth_date:
                event_line += f" {self._convert_date_to_gw(person.birth_date)}"
            if person.birth_place:
                event_line += f" #p {person.birth_place}"
            lines.append(event_line)

        if person.death_date or person.death_place:
            event_line = "#deat"
            if person.death_date:
                event_line += f" {self._convert_date_to_gw(person.death_date)}"
            if person.death_place:
                event_line += f" #p {person.death_place}"
            lines.append(event_line)

        # Other events
        events = (
            self.db.query(self.Event).filter(self.Event.person_id == person.id).all()
        )

        for event in events:
            if event.event_type not in ["BIRT", "DEAT"]:
                event_line = f"#{event.event_type.lower()}"
                if event.date:
                    event_line += f" {self._convert_date_to_gw(event.date)}"
                if event.place:
                    event_line += f" #p {event.place}"
                lines.append(event_line)

        lines.append("end pevt")

    def _convert_date_to_gw(self, date_str: str) -> str:
        """Convert date from database format to GeneWeb format."""
        if not date_str:
            return ""

        # Remove extra spaces
        date_str = date_str.strip()

        # Handle special prefixes
        if date_str.startswith("BEF ") or date_str.startswith("Avant "):
            year = date_str.split()[-1]
            return f"<{year}"

        if date_str.startswith("AFT ") or date_str.startswith("Après "):
            year = date_str.split()[-1]
            return f">{year}"

        # Try to parse "DD MMM YYYY" format
        parts = date_str.split()
        if len(parts) >= 3:
            day = parts[0]
            month_str = parts[1].upper()
            year = parts[2]

            months = {
                "JAN": "1",
                "FEB": "2",
                "MAR": "3",
                "APR": "4",
                "MAY": "5",
                "JUN": "6",
                "JUL": "7",
                "AUG": "8",
                "SEP": "9",
                "OCT": "10",
                "NOV": "11",
                "DEC": "12",
            }

            if month_str in months:
                return f"{day}/{months[month_str]}/{year}"

        return date_str
