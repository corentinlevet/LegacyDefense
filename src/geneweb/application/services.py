import os
import tempfile
from datetime import date
from typing import Optional

from gedcom.element.family import FamilyElement
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser as GedcomParser
from sqlalchemy.orm import Session

from ..infrastructure.database import SessionLocal
from ..infrastructure.models import Event, Family, Genealogy, Person


def _format_date_for_gedcom(d: Optional[object]) -> Optional[str]:
    """
    Convertit une date Python (date, datetime) ou string en format GEDCOM simple "DD MON YYYY".
    Si l'entrée est déjà une string, on la renvoie telle quelle (assume format acceptable).
    """
    if d is None:
        return None
    # Si c'est un objet date/datetime
    try:
        if hasattr(d, "strftime"):
            return d.strftime("%d %b %Y").upper()  # e.g. "01 JAN 1900"
    except Exception:
        pass
    # Sinon on suppose que c'est une string
    return str(d)


class GenealogyService:
    def create_genealogy(self, name: str, force: bool = False):
        """
        Creates a new genealogy.

        :param name: The name of the genealogy.
        :param force: If True, deletes the existing genealogy and its data.
        """
        db: Session = SessionLocal()
        try:
            existing_genealogy = (
                db.query(Genealogy).filter(Genealogy.name == name).first()
            )

            if existing_genealogy:
                if not force:
                    print(
                        f"Genealogy '{name}' already exists. Use --force to overwrite."
                    )
                    return
                else:
                    print(f"Deleting existing genealogy '{name}'...")
                    db.delete(existing_genealogy)
                    db.commit()  # Commit the deletion

            print(f"Creating new genealogy '{name}'...")
            new_genealogy = Genealogy(name=name)
            db.add(new_genealogy)
            db.commit()
            print(f"Genealogy '{name}' created successfully.")
            return new_genealogy

        finally:
            db.close()

    def get_all_genealogies(self):
        """
        Retrieves all genealogies.
        """
        db: Session = SessionLocal()
        try:
            genealogies = db.query(Genealogy).all()
            return genealogies
        finally:
            db.close()

    def import_gedcom(self, genealogy_name: str, gedcom_content: str, db: Session):
        """
        Parses GEDCOM content and populates the database for a specific genealogy.
        """
        genealogy = db.query(Genealogy).filter(Genealogy.name == genealogy_name).first()
        if not genealogy:
            raise ValueError(f"Genealogy '{genealogy_name}' not found.")

        # Créer un fichier temporaire pour le parser GEDCOM
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ged", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(gedcom_content)
            tmp_file_path = tmp_file.name

        try:
            # Créer le parser et charger le contenu GEDCOM
            parser = GedcomParser()
            parser.parse_file(tmp_file_path)

            # Récupérer les individus et familles depuis le dictionnaire d'éléments
            element_dict = parser.get_element_dictionary()
            gedcom_individuals = {
                k: v
                for k, v in element_dict.items()
                if isinstance(v, IndividualElement)
            }
            gedcom_families = {
                k: v for k, v in element_dict.items() if isinstance(v, FamilyElement)
            }

            # Maps GEDCOM ID to our Person/Family object
            person_map = {}
            family_map = {}

            # --- Pass 1: Create Persons ---
            for gedcom_id, gedcom_indi in gedcom_individuals.items():
                first_name = ""
                surname = ""
                name_record = gedcom_indi.get_child_elements()
                for child in name_record:
                    if child.get_tag() == "NAME":
                        full_name = child.get_value()
                        parts = full_name.split("/")
                        if len(parts) == 3:  # e.g., Given /Surname/
                            first_name = parts[0].strip()
                            surname = parts[1].strip()
                        elif len(parts) == 2:  # e.g., /Surname/
                            surname = parts[1].strip() if parts[1] else parts[0].strip()
                        else:  # e.g., Full Name
                            first_name = full_name
                        break

                sex = "U"
                for child in gedcom_indi.get_child_elements():
                    if child.get_tag() == "SEX":
                        sex = child.get_value()
                        break

                person = Person(
                    genealogy_id=genealogy.id,
                    first_name=first_name,
                    surname=surname,
                    sex=sex,
                )
                db.add(person)
                person_map[gedcom_id] = person

            db.flush()  # Flush to assign IDs to persons

            # --- Pass 2: Add Person Details and Events ---
            for gedcom_id, gedcom_indi in gedcom_individuals.items():
                person = person_map[gedcom_id]

                for child_element in gedcom_indi.get_child_elements():
                    tag = child_element.get_tag()

                    # Birth Event
                    if tag == "BIRT":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        person.birth_date = date_val
                        person.birth_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                person_id=person.id,
                                event_type="BIRT",
                                date=date_val,
                                place=place_val,
                            )
                        )

                    # Death Event
                    elif tag == "DEAT":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        person.death_date = date_val
                        person.death_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                person_id=person.id,
                                event_type="DEAT",
                                date=date_val,
                                place=place_val,
                            )
                        )

                    # Occupation
                    elif tag == "OCCU":
                        person.occupation = child_element.get_value()

                    # Notes
                    elif tag == "NOTE":
                        person.notes = child_element.get_value()

                    # Baptism
                    elif tag == "BAPM":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        person.baptism_date = date_val
                        person.baptism_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                person_id=person.id,
                                event_type="BAPM",
                                date=date_val,
                                place=place_val,
                            )
                        )

                    # Burial
                    elif tag == "BURI":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        person.burial_date = date_val
                        person.burial_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                person_id=person.id,
                                event_type="BURI",
                                date=date_val,
                                place=place_val,
                            )
                        )

            # --- Pass 3: Create Families and link members ---
            for gedcom_id, gedcom_fam in gedcom_families.items():
                husband_id = None
                wife_id = None

                for child in gedcom_fam.get_child_elements():
                    if child.get_tag() == "HUSB":
                        husband_id = child.get_value()
                    elif child.get_tag() == "WIFE":
                        wife_id = child.get_value()

                family = Family(
                    genealogy_id=genealogy.id,
                    father_id=(
                        person_map[husband_id].id
                        if husband_id and husband_id in person_map
                        else None
                    ),
                    mother_id=(
                        person_map[wife_id].id
                        if wife_id and wife_id in person_map
                        else None
                    ),
                )
                db.add(family)
                family_map[gedcom_id] = family

            db.flush()  # Flush to assign IDs to families

            # --- Pass 4: Add Family Details and Events, link children ---
            for gedcom_id, gedcom_fam in gedcom_families.items():
                family = family_map[gedcom_id]

                for child_element in gedcom_fam.get_child_elements():
                    tag = child_element.get_tag()

                    # Marriage Event
                    if tag == "MARR":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        family.marriage_date = date_val
                        family.marriage_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                family_id=family.id,
                                event_type="MARR",
                                date=date_val,
                                place=place_val,
                            )
                        )

                    # Divorce Event
                    elif tag == "DIV":
                        date_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()

                        family.divorce_date = date_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                family_id=family.id,
                                event_type="DIV",
                                date=date_val,
                            )
                        )

                    # Children
                    elif tag == "CHIL":
                        child_id = child_element.get_value()
                        if child_id and child_id in person_map:
                            family.children.append(person_map[child_id])

            db.commit()
            print(f"GEDCOM content imported into genealogy '{genealogy.name}'.")
        finally:
            # Supprimer le fichier temporaire
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    def export_gedcom(self, genealogy_id: int, db: Session) -> str:
        """
        Génère une chaîne GEDCOM 5.5.1 à partir de la base pour une généalogie donnée.
        """
        genealogy = db.query(Genealogy).filter(Genealogy.id == genealogy_id).first()
        if not genealogy:
            raise ValueError(f"Genealogy with ID {genealogy_id} not found.")

        # Récupérer données
        persons = db.query(Person).filter(Person.genealogy_id == genealogy_id).all()
        families = db.query(Family).filter(Family.genealogy_id == genealogy_id).all()

        # Maps DB id -> GEDCOM id
        person_ged_id = {p.id: f"@I{p.id}@" for p in persons}
        family_ged_id = {f.id: f"@F{f.id}@" for f in families}

        lines = []

        # Header
        lines.append("0 HEAD")
        lines.append("1 SOUR GeneWeb Modernization")
        lines.append(f"1 DATE {date.today().strftime('%d %b %Y').upper()}")
        lines.append(f"1 FILE {genealogy.name}.ged")
        lines.append("1 GEDC")
        lines.append("2 VERS 5.5.1")
        lines.append("2 FORM LINEAGE-LINKED")
        lines.append("1 CHAR UTF-8")
        # Individuals
        for p in persons:
            gid = person_ged_id[p.id]
            lines.append(f"0 {gid} INDI")

            # Name
            # GEDCOM wants Given /Surname/
            given = (p.first_name or "").strip()
            surname = (p.surname or "").strip()
            if given and surname:
                name_line = f"{given} /{surname}/"
            elif surname:
                name_line = f"/{surname}/"
            elif given:
                name_line = given
            else:
                name_line = "Unknown"
            lines.append(f"1 NAME {name_line}")

            # Optional Individual name parts (GIVN, SURN)
            if given:
                lines.append(f"2 GIVN {given}")
            if surname:
                lines.append(f"2 SURN {surname}")

            # Sex
            if getattr(p, "sex", None):
                # si p.sex est un Enum, prendre sa valeur ou son nom
                sex_val = p.sex.value if hasattr(p.sex, "value") else str(p.sex)
                lines.append(f"1 SEX {sex_val}")

            # Birth
            bdate = _format_date_for_gedcom(getattr(p, "birth_date", None))
            bplace = getattr(p, "birth_place", None)
            if bdate or bplace:
                lines.append("1 BIRT")
                if bdate:
                    lines.append(f"2 DATE {bdate}")
                if bplace:
                    lines.append(f"2 PLAC {bplace}")

            # Death
            ddate = _format_date_for_gedcom(getattr(p, "death_date", None))
            dplace = getattr(p, "death_place", None)
            if ddate or dplace:
                lines.append("1 DEAT")
                if ddate:
                    lines.append(f"2 DATE {ddate}")
                if dplace:
                    lines.append(f"2 PLAC {dplace}")

            # Baptism (BAPM)
            bapm_date = _format_date_for_gedcom(getattr(p, "baptism_date", None))
            bapm_place = getattr(p, "baptism_place", None)
            if bapm_date or bapm_place:
                lines.append("1 BAPM")
                if bapm_date:
                    lines.append(f"2 DATE {bapm_date}")
                if bapm_place:
                    lines.append(f"2 PLAC {bapm_place}")

            # Burial (BURI)
            buri_date = _format_date_for_gedcom(getattr(p, "burial_date", None))
            buri_place = getattr(p, "burial_place", None)
            if buri_date or buri_place:
                lines.append("1 BURI")
                if buri_date:
                    lines.append(f"2 DATE {buri_date}")
                if buri_place:
                    lines.append(f"2 PLAC {buri_place}")

            # Occupation
            if getattr(p, "occupation", None):
                lines.append(f"1 OCCU {p.occupation}")

            # Notes
            if getattr(p, "notes", None):
                # Note lines may be multi-line: on peut split \n et indenter niveau 2
                note = str(p.notes)
                for i, nl in enumerate(note.splitlines() or [""]):
                    if i == 0:
                        lines.append(f"1 NOTE {nl}")
                    else:
                        lines.append(f"2 CONT {nl}")

            # FAMC: familles où il/elle est enfant
            # On suppose existence d'une relation person.child_of_families ou équivalent.
            child_of = getattr(p, "child_of_families", None)
            if child_of:
                for fam in child_of:
                    if fam and fam.id in family_ged_id:
                        lines.append(f"1 FAMC {family_ged_id[fam.id]}")

            # FAMS: familles où il/elle est époux(se)
            # On peut déterminer par families list: families where father_id/mother_id == person.id
            for fam in families:
                if (getattr(fam, "father_id", None) == p.id) or (
                    getattr(fam, "mother_id", None) == p.id
                ):
                    lines.append(f"1 FAMS {family_ged_id[fam.id]}")

        # Families
        for fam in families:
            fid = family_ged_id[fam.id]
            lines.append(f"0 {fid} FAM")

            # Husband / Wife
            if getattr(fam, "father_id", None) and fam.father_id in person_ged_id:
                lines.append(f"1 HUSB {person_ged_id[fam.father_id]}")
            if getattr(fam, "mother_id", None) and fam.mother_id in person_ged_id:
                lines.append(f"1 WIFE {person_ged_id[fam.mother_id]}")

            # Children
            # On suppose relation fam.children contenant Person instances
            children = getattr(fam, "children", None) or []
            for c in children:
                if c and c.id in person_ged_id:
                    lines.append(f"1 CHIL {person_ged_id[c.id]}")

            # Marriage
            marr_date = _format_date_for_gedcom(getattr(fam, "marriage_date", None))
            marr_place = getattr(fam, "marriage_place", None)
            if marr_date or marr_place:
                lines.append("1 MARR")
                if marr_date:
                    lines.append(f"2 DATE {marr_date}")
                if marr_place:
                    lines.append(f"2 PLAC {marr_place}")

            # Divorce
            if getattr(fam, "divorce_date", None):
                div_date = _format_date_for_gedcom(getattr(fam, "divorce_date", None))
                lines.append("1 DIV")
                if div_date:
                    lines.append(f"2 DATE {div_date}")

            # Family notes
            if getattr(fam, "marriage_note", None):
                note = str(fam.marriage_note)
                for i, nl in enumerate(note.splitlines() or [""]):
                    if i == 0:
                        lines.append(f"1 NOTE {nl}")
                    else:
                        lines.append(f"2 CONT {nl}")

        # Trailer
        lines.append("0 TRLR")

        # Join with CRLF or LF: GEDCOM accepte LF. On utilise \n.
        gedcom_text = "\n".join(lines) + "\n"
        return gedcom_text
