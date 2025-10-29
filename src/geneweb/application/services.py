import os
import re
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from fastapi import logger
from gedcom.element.family import FamilyElement
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser as GedcomParser
from sqlalchemy.orm import Session

from ..infrastructure.database import SessionLocal
from ..infrastructure.models import Event, Family, Genealogy, Person
from ..infrastructure.repositories.sql_genealogy_repository import (
    SQLGenealogyRepository,
)
from ..presentation.web.formatters import format_date_natural


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


def parse_date_for_sorting(date_str: str | None) -> tuple[int, int, int]:
    """
    Parse une date stockée en texte et retourne un tuple (année, mois, jour) pour le tri.
    Gère les formats: "Avant YYYY", "Entre YYYY et YYYY", "Estimé YYYY", "DD Month YYYY", etc.

    Retourne (9999, 12, 31) pour les dates invalides (les mettra en dernier)
    """
    if not date_str:
        return (9999, 12, 31)

    date_str = date_str.strip()

    # Avant YYYY -> utilise l'année moins 1
    if date_str.startswith("Avant") or date_str.startswith("Before"):
        match = re.search(r"\d{4}", date_str)
        if match:
            year = int(match.group()) - 1
            return (year, 12, 31)

    # Estimé YYYY / About YYYY -> utilise l'année
    if date_str.startswith("Estimé") or date_str.startswith("About"):
        match = re.search(r"\d{4}", date_str)
        if match:
            year = int(match.group())
            return (year, 6, 15)  # Milieu de l'année

    # Entre YYYY et YYYY -> utilise la première année
    if date_str.startswith("Entre") or date_str.startswith("Between"):
        match = re.search(r"\d{4}", date_str)
        if match:
            year = int(match.group())
            return (year, 1, 1)

    # Format complet: "DD Month YYYY" ou "DD/MM/YYYY"
    try:
        # Essaie différents formats de date
        for fmt in ["%d %B %Y", "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return (dt.year, dt.month, dt.day)
            except ValueError:
                continue
    except:
        logger.exception("Error parsing date")
        pass

    # Juste une année: "YYYY"
    match = re.search(r"\b(\d{4})\b", date_str)
    if match:
        year = int(match.group(1))
        return (year, 1, 1)

    return (9999, 12, 31)


def is_possibly_alive(birth_date_str: str | None, death_date_str: str | None) -> bool:
    """
    Détermine si une personne peut plausiblement être encore en vie.

    Critères:
    - Pas de date de décès enregistrée
    - Date de naissance dans les 120 dernières années (âge maximum plausible)
    """
    if death_date_str:
        return False

    if not birth_date_str:
        return False

    birth_tuple = parse_date_for_sorting(birth_date_str)
    if birth_tuple[0] == 9999:  # Date invalide
        return False

    current_year = datetime.now().year
    age = current_year - birth_tuple[0]

    # Une personne de plus de 120 ans est considérée comme décédée
    return age <= 120


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


@dataclass
class GenealogyDetails:
    name: str
    person_count: int


class ApplicationService:
    def __init__(self, genealogy_repo: SQLGenealogyRepository):
        self.genealogy_repo = genealogy_repo

    async def get_genealogy_details(self, name: str) -> GenealogyDetails | None:
        genealogy = self.genealogy_repo.get_by_name(name)
        if not genealogy:
            return None

        person_count = self.genealogy_repo.count_persons(genealogy.id)

        return GenealogyDetails(name=genealogy.name, person_count=person_count)

    async def get_first_names(self, genealogy_name: str) -> list[str] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        return self.genealogy_repo.get_first_names(genealogy.id)

    async def get_last_names(self, genealogy_name: str) -> list[str] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        return self.genealogy_repo.get_last_names(genealogy.id)

    async def get_places(self, genealogy_name: str) -> list[str] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        return self.genealogy_repo.get_places(genealogy.id)

    async def get_occupations(self, genealogy_name: str) -> list[str] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        return self.genealogy_repo.get_occupations(genealogy.id)

    async def get_sources(self, genealogy_name: str) -> list[str] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        return self.genealogy_repo.get_sources(genealogy.id)

    async def get_last_births(
        self, genealogy_name: str, limit: int = 20
    ) -> list[dict] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        # Utilise SessionLocal pour créer une session
        from ..infrastructure.database import SessionLocal

        db = SessionLocal()
        try:
            # Récupère TOUTES les personnes avec date de naissance
            all_persons = (
                db.query(Person)
                .filter(
                    Person.genealogy_id == genealogy.id, Person.birth_date.isnot(None)
                )
                .all()
            )

            # Trie par date de naissance décroissante (plus récent en premier)
            sorted_persons = sorted(
                all_persons,
                key=lambda p: parse_date_for_sorting(p.birth_date),
                reverse=True,
            )

            # Limite aux N premiers
            persons = sorted_persons[:limit]

            return [
                {
                    "id": person.id,
                    "first_name": person.first_name,
                    "surname": person.surname,
                    "birth_date": format_date_natural(person.birth_date),
                }
                for person in persons
            ]
        finally:
            db.close()

    async def get_last_deaths(
        self, genealogy_name: str, limit: int = 20
    ) -> list[dict] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        from ..infrastructure.database import SessionLocal

        db = SessionLocal()
        try:
            all_persons = (
                db.query(Person)
                .filter(
                    Person.genealogy_id == genealogy.id, Person.death_date.isnot(None)
                )
                .all()
            )

            sorted_persons = sorted(
                all_persons,
                key=lambda p: parse_date_for_sorting(p.death_date),
                reverse=True,
            )

            persons = sorted_persons[:limit]

            return [
                {
                    "id": person.id,
                    "first_name": person.first_name,
                    "surname": person.surname,
                    "death_date": format_date_natural(person.death_date),
                }
                for person in persons
            ]
        finally:
            db.close()

    async def get_last_marriages(
        self, genealogy_name: str, limit: int = 20
    ) -> list[dict] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        from ..infrastructure.database import SessionLocal

        db = SessionLocal()
        try:
            all_families = (
                db.query(Family)
                .filter(
                    Family.genealogy_id == genealogy.id,
                    Family.marriage_date.isnot(None),
                )
                .all()
            )

            sorted_families = sorted(
                all_families,
                key=lambda f: parse_date_for_sorting(f.marriage_date),
                reverse=True,
            )

            families = sorted_families[:limit]

            return [
                {
                    "id": family.id,
                    "father_first_name": (
                        family.father.first_name if family.father else ""
                    ),
                    "father_surname": family.father.surname if family.father else "",
                    "mother_first_name": (
                        family.mother.first_name if family.mother else ""
                    ),
                    "mother_surname": family.mother.surname if family.mother else "",
                    "marriage_date": format_date_natural(family.marriage_date),
                }
                for family in families
            ]
        finally:
            db.close()

    async def get_oldest_couples(
        self, genealogy_name: str, limit: int = 20
    ) -> list[dict] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        from ..infrastructure.database import SessionLocal

        db = SessionLocal()
        try:
            # Récupère toutes les familles avec date de mariage
            all_families = (
                db.query(Family)
                .filter(
                    Family.genealogy_id == genealogy.id,
                    Family.marriage_date.isnot(None),
                )
                .all()
            )

            alive_couples = []
            for family in all_families:
                # Vérifie que les deux conjoints existent et peuvent être en vie
                if (
                    family.father
                    and family.mother
                    and is_possibly_alive(
                        family.father.birth_date, family.father.death_date
                    )
                    and is_possibly_alive(
                        family.mother.birth_date, family.mother.death_date
                    )
                ):
                    alive_couples.append(
                        {
                            "id": family.id,
                            "father_first_name": family.father.first_name,
                            "father_surname": family.father.surname,
                            "mother_first_name": family.mother.first_name,
                            "mother_surname": family.mother.surname,
                            "marriage_date": format_date_natural(family.marriage_date),
                        }
                    )

            # Trie par date de mariage croissante (les plus anciens mariages en premier)
            sorted_couples = sorted(
                alive_couples,
                key=lambda x: parse_date_for_sorting(x["marriage_date"]),
                reverse=False,
            )

            return sorted_couples[:limit]
        finally:
            db.close()

    async def get_oldest_alive(
        self, genealogy_name: str, limit: int = 20
    ) -> list[dict] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        from ..infrastructure.database import SessionLocal

        db = SessionLocal()
        try:
            # Récupère toutes les personnes avec date de naissance
            all_persons = (
                db.query(Person)
                .filter(
                    Person.genealogy_id == genealogy.id,
                    Person.birth_date.isnot(None),
                )
                .all()
            )

            # Filtre les personnes qui peuvent plausiblement être en vie
            alive_persons = [
                p for p in all_persons if is_possibly_alive(p.birth_date, p.death_date)
            ]

            # Trie par date de naissance croissante (les plus vieux en premier)
            sorted_persons = sorted(
                alive_persons,
                key=lambda p: parse_date_for_sorting(p.birth_date),
                reverse=False,
            )

            # Limite aux N premiers et élimine les doublons par ID
            seen_ids = set()
            unique_persons = []
            for person in sorted_persons:
                if person.id not in seen_ids:
                    seen_ids.add(person.id)
                    unique_persons.append(
                        {
                            "id": person.id,
                            "first_name": person.first_name,
                            "surname": person.surname,
                            "birth_date": format_date_natural(person.birth_date),
                        }
                    )
                if len(unique_persons) >= limit:
                    break

            return unique_persons
        finally:
            db.close()

    async def get_longest_lived(
        self, genealogy_name: str, limit: int = 20
    ) -> list[dict] | None:
        genealogy = self.genealogy_repo.get_by_name(genealogy_name)
        if not genealogy:
            return None

        from ..infrastructure.database import SessionLocal

        db = SessionLocal()
        try:
            # Récupère toutes les personnes avec date de naissance ET de décès
            all_persons = (
                db.query(Person)
                .filter(
                    Person.genealogy_id == genealogy.id,
                    Person.birth_date.isnot(None),
                    Person.death_date.isnot(None),
                )
                .all()
            )

            longest_lived = []
            for person in all_persons:
                birth_tuple = parse_date_for_sorting(person.birth_date)
                death_tuple = parse_date_for_sorting(person.death_date)

                # Calcule l'âge approximatif en années
                if birth_tuple[0] != 9999 and death_tuple[0] != 9999:
                    age = death_tuple[0] - birth_tuple[0]
                    # Ajuste si le mois/jour de décès est avant le mois/jour de naissance
                    if (death_tuple[1], death_tuple[2]) < (
                        birth_tuple[1],
                        birth_tuple[2],
                    ):
                        age -= 1

                    longest_lived.append(
                        {
                            "id": person.id,
                            "first_name": person.first_name,
                            "surname": person.surname,
                            "birth_date": format_date_natural(person.birth_date),
                            "death_date": format_date_natural(person.death_date),
                            "age": age,
                        }
                    )

            # Trie par âge décroissant (les plus vieux en premier)
            sorted_persons = sorted(longest_lived, key=lambda x: x["age"], reverse=True)

            return sorted_persons[:limit]
        finally:
            db.close()
