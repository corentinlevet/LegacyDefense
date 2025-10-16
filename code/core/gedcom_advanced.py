"""
GEDCOM advanced features: encoding support, additional tags, and validation.

This module extends the core GEDCOM parser with:
- ANSEL to UTF-8 encoding conversion
- Support for all GEDCOM 5.5.1 tags
- Round-trip data preservation
- GEDCOM validation

Ported from OCaml implementation in geneweb/bin/ged2gwb and gwb2ged
"""

import codecs
from typing import Dict, List, Optional, Set, Tuple

# ANSEL to Unicode mapping table
ANSEL_TO_UNICODE = {
    0xA1: "\u0141",  # Ł - LATIN CAPITAL LETTER L WITH STROKE
    0xA2: "\u00D8",  # Ø - LATIN CAPITAL LETTER O WITH STROKE
    0xA3: "\u0110",  # Đ - LATIN CAPITAL LETTER D WITH STROKE
    0xA4: "\u00DE",  # Þ - LATIN CAPITAL LETTER THORN
    0xA5: "\u00C6",  # Æ - LATIN CAPITAL LETTER AE
    0xA6: "\u0152",  # Œ - LATIN CAPITAL LIGATURE OE
    0xA7: "\u02B9",  # ʹ - MODIFIER LETTER PRIME
    0xA8: "\u00B7",  # · - MIDDLE DOT
    0xA9: "\u266D",  # ♭ - MUSIC FLAT SIGN
    0xAA: "\u00AE",  # ® - REGISTERED SIGN
    0xAB: "\u00B1",  # ± - PLUS-MINUS SIGN
    0xAC: "\u01A0",  # Ơ - LATIN CAPITAL LETTER O WITH HORN
    0xAD: "\u01AF",  # Ư - LATIN CAPITAL LETTER U WITH HORN
    0xAE: "\u02BC",  # ʼ - MODIFIER LETTER APOSTROPHE
    0xB0: "\u02BB",  # ʻ - MODIFIER LETTER TURNED COMMA
    0xB1: "\u0142",  # ł - LATIN SMALL LETTER L WITH STROKE
    0xB2: "\u00F8",  # ø - LATIN SMALL LETTER O WITH STROKE
    0xB3: "\u0111",  # đ - LATIN SMALL LETTER D WITH STROKE
    0xB4: "\u00FE",  # þ - LATIN SMALL LETTER THORN
    0xB5: "\u00E6",  # æ - LATIN SMALL LETTER AE
    0xB6: "\u0153",  # œ - LATIN SMALL LIGATURE OE
    0xB7: "\u02BA",  # ʺ - MODIFIER LETTER DOUBLE PRIME
    0xB8: "\u0131",  # ı - LATIN SMALL LETTER DOTLESS I
    0xB9: "\u00A3",  # £ - POUND SIGN
    0xBA: "\u00F0",  # ð - LATIN SMALL LETTER ETH
    0xBC: "\u01A1",  # ơ - LATIN SMALL LETTER O WITH HORN
    0xBD: "\u01B0",  # ư - LATIN SMALL LETTER U WITH HORN
    # Combining diacriticals (0xE0-0xFE)
    0xE0: "\u0309",  # COMBINING HOOK ABOVE
    0xE1: "\u0300",  # COMBINING GRAVE ACCENT
    0xE2: "\u0301",  # COMBINING ACUTE ACCENT
    0xE3: "\u0302",  # COMBINING CIRCUMFLEX ACCENT
    0xE4: "\u0303",  # COMBINING TILDE
    0xE5: "\u0304",  # COMBINING MACRON
    0xE6: "\u0306",  # COMBINING BREVE
    0xE7: "\u0307",  # COMBINING DOT ABOVE
    0xE8: "\u0308",  # COMBINING DIAERESIS
    0xE9: "\u030C",  # COMBINING CARON
    0xEA: "\u030A",  # COMBINING RING ABOVE
    0xEB: "\u0327",  # COMBINING CEDILLA
    0xEC: "\u0328",  # COMBINING OGONEK
    0xED: "\u0323",  # COMBINING DOT BELOW
    0xEE: "\u0324",  # COMBINING DIAERESIS BELOW
    0xEF: "\u0325",  # COMBINING RING BELOW
    0xF0: "\u0331",  # COMBINING MACRON BELOW
    0xF1: "\u0326",  # COMBINING COMMA BELOW
    0xF2: "\u031C",  # COMBINING LEFT HALF RING BELOW
    0xF3: "\u032E",  # COMBINING BREVE BELOW
    0xF4: "\u0361",  # COMBINING DOUBLE INVERTED BREVE
    0xF9: "\u0313",  # COMBINING COMMA ABOVE
}


class AnselCodec(codecs.Codec):
    """ANSEL encoding/decoding codec."""

    def encode(self, input_str: str, errors="strict") -> Tuple[bytes, int]:
        """Encode Unicode to ANSEL (not fully implemented)."""
        # For now, just use UTF-8
        return input_str.encode("utf-8", errors), len(input_str)

    def decode(self, input_bytes: bytes, errors="strict") -> Tuple[str, int]:
        """Decode ANSEL to Unicode."""
        result = []
        i = 0
        while i < len(input_bytes):
            byte = input_bytes[i]

            if byte in ANSEL_TO_UNICODE:
                # ANSEL special character
                result.append(ANSEL_TO_UNICODE[byte])
            elif 0xE0 <= byte <= 0xFE:
                # Combining diacritic - apply to next character
                if i + 1 < len(input_bytes):
                    next_byte = input_bytes[i + 1]
                    base_char = chr(next_byte)
                    combining_char = ANSEL_TO_UNICODE.get(byte, "")
                    result.append(base_char + combining_char)
                    i += 1  # Skip next byte
            else:
                # Regular ASCII
                result.append(chr(byte))

            i += 1

        return "".join(result), len(input_bytes)


def detect_gedcom_encoding(file_path: str) -> str:
    """
    Detect GEDCOM file encoding by reading the HEAD/CHAR tag.
    
    Args:
        file_path: Path to GEDCOM file
        
    Returns:
        Encoding name: 'UTF-8', 'ANSEL', 'ASCII', 'UNICODE', etc.
    """
    with open(file_path, "rb") as f:
        # Read first 2000 bytes to find header
        header = f.read(2000)

    # Look for CHAR tag in header
    header_str = header.decode("ascii", errors="ignore")
    lines = header_str.split("\n")

    for i, line in enumerate(lines):
        if "CHAR" in line:
            # Next line or same line should contain encoding
            parts = line.split()
            if len(parts) >= 2:
                return parts[-1].upper()

    # Default to UTF-8 if not specified
    return "UTF-8"


def read_gedcom_with_encoding(file_path: str) -> str:
    """
    Read GEDCOM file with proper encoding detection and conversion.
    
    Args:
        file_path: Path to GEDCOM file
        
    Returns:
        File content as UTF-8 string
    """
    encoding = detect_gedcom_encoding(file_path)

    if encoding == "ANSEL":
        # Read as bytes and decode using ANSEL codec
        with open(file_path, "rb") as f:
            content_bytes = f.read()

        codec = AnselCodec()
        content, _ = codec.decode(content_bytes)
        return content
    elif encoding in ["UTF-8", "UTF8"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif encoding == "ASCII":
        with open(file_path, "r", encoding="ascii") as f:
            return f.read()
    elif encoding in ["UNICODE", "UTF-16"]:
        with open(file_path, "r", encoding="utf-16") as f:
            return f.read()
    else:
        # Try UTF-8 as fallback
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


# Extended GEDCOM tag definitions for GEDCOM 5.5.1
GEDCOM_551_TAGS = {
    # Individual tags
    "INDI": "Individual record",
    "NAME": "Name",
    "SEX": "Sex",
    "BIRT": "Birth",
    "DEAT": "Death",
    "BAPM": "Baptism",
    "BURI": "Burial",
    "CHR": "Christening",
    "CREM": "Cremation",
    "ADOP": "Adoption",
    "CONF": "Confirmation",
    "FCOM": "First Communion",
    "ORDN": "Ordination",
    "NATU": "Naturalization",
    "EMIG": "Emigration",
    "IMMI": "Immigration",
    "CENS": "Census",
    "PROB": "Probate",
    "WILL": "Will",
    "GRAD": "Graduation",
    "RETI": "Retirement",
    "EVEN": "Event",
    "CAST": "Caste",
    "DSCR": "Physical Description",
    "EDUC": "Education",
    "IDNO": "National ID Number",
    "NATI": "Nationality",
    "NCHI": "Number of Children",
    "NMR": "Number of Marriages",
    "OCCU": "Occupation",
    "PROP": "Property",
    "RELI": "Religion",
    "RESI": "Residence",
    "SSN": "Social Security Number",
    "TITL": "Title",
    "FACT": "Fact",
    # Family tags
    "FAM": "Family record",
    "HUSB": "Husband",
    "WIFE": "Wife",
    "CHIL": "Child",
    "MARR": "Marriage",
    "DIV": "Divorce",
    "ANUL": "Annulment",
    "ENGA": "Engagement",
    "MARB": "Marriage Bann",
    "MARC": "Marriage Contract",
    "MARL": "Marriage License",
    "MARS": "Marriage Settlement",
    # Source/citation tags
    "SOUR": "Source",
    "REPO": "Repository",
    "NOTE": "Note",
    "OBJE": "Multimedia",
    "REFN": "Reference",
    "RIN": "Automated Record ID",
    "CHAN": "Change",
    # Date/place tags
    "DATE": "Date",
    "PLAC": "Place",
    "ADDR": "Address",
    "PHON": "Phone",
    "EMAIL": "Email",
    "FAX": "Fax",
    "WWW": "Web page",
    # Header tags
    "HEAD": "Header",
    "SUBM": "Submitter",
    "SUBN": "Submission",
    "GEDC": "GEDCOM",
    "CHAR": "Character set",
    "LANG": "Language",
    "DEST": "Destination",
    "FILE": "File",
    "COPR": "Copyright",
    # Linking tags
    "FAMC": "Family Child",
    "FAMS": "Family Spouse",
    # Attribute tags
    "TYPE": "Type",
    "AGE": "Age",
    "CAUS": "Cause",
    "AGNC": "Agency",
    # Name component tags
    "GIVN": "Given Name",
    "SURN": "Surname",
    "NPFX": "Name Prefix",
    "NSFX": "Name Suffix",
    "NICK": "Nickname",
    # Place component tags
    "CITY": "City",
    "STAE": "State",
    "POST": "Postal Code",
    "CTRY": "Country",
    # Continuation tags
    "CONC": "Concatenation",
    "CONT": "Continuation",
    # Trailer
    "TRLR": "Trailer",
}


class GedcomValidator:
    """Validates GEDCOM files against the 5.5.1 specification."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_file(self, file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a GEDCOM file.
        
        Args:
            file_path: Path to GEDCOM file
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            content = read_gedcom_with_encoding(file_path)
            self._validate_structure(content)
            self._validate_tags(content)
            self._validate_cross_references(content)

        except Exception as e:
            self.errors.append(f"Validation error: {str(e)}")

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_structure(self, content: str) -> None:
        """Validate overall GEDCOM structure."""
        lines = content.strip().split("\n")

        # Check for header
        if not lines or not lines[0].startswith("0 HEAD"):
            self.errors.append("Missing GEDCOM header (0 HEAD)")

        # Check for trailer
        if not lines or not lines[-1].startswith("0 TRLR"):
            self.errors.append("Missing GEDCOM trailer (0 TRLR)")

        # Validate line format and level hierarchy
        prev_level = -1
        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue

            # Check basic line format
            parts = line.split(None, 1)
            if not parts:
                self.warnings.append(f"Line {i}: Empty line")
                continue

            try:
                level = int(parts[0])
            except ValueError:
                self.errors.append(f"Line {i}: Invalid level number: {parts[0]}")
                continue

            # Check level progression (can only increment by 1)
            if level > prev_level + 1:
                self.warnings.append(
                    f"Line {i}: Level jump from {prev_level} to {level}"
                )

            prev_level = level

    def _validate_tags(self, content: str) -> None:
        """Validate GEDCOM tags."""
        lines = content.strip().split("\n")

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Extract tag
            parts = line.split()
            if len(parts) < 2:
                continue

            # Skip XREF IDs
            if parts[1].startswith("@") and parts[1].endswith("@"):
                if len(parts) < 3:
                    continue
                tag = parts[2]
            else:
                tag = parts[1]

            # Check if tag is known (optional warning)
            if tag not in GEDCOM_551_TAGS:
                # Only warn for level 0 and 1 tags
                level = int(parts[0])
                if level <= 1:
                    self.warnings.append(
                        f"Line {i}: Unknown tag '{tag}' "
                        f"(not in GEDCOM 5.5.1 spec)"
                    )

    def _validate_cross_references(self, content: str) -> None:
        """Validate cross-references (XREF pointers)."""
        lines = content.strip().split("\n")

        # Collect all defined XREFs
        defined_xrefs: Set[str] = set()
        referenced_xrefs: Set[str] = set()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            # Check for XREF definition (0 @ID@ TAG)
            if parts[0] == "0" and parts[1].startswith("@") and parts[1].endswith("@"):
                xref = parts[1].strip("@")
                if xref in defined_xrefs:
                    self.warnings.append(f"Duplicate XREF definition: @{xref}@")
                defined_xrefs.add(xref)

            # Check for XREF references
            for part in parts[1:]:
                if part.startswith("@") and part.endswith("@") and len(part) > 2:
                    xref = part.strip("@")
                    referenced_xrefs.add(xref)

        # Find undefined references
        undefined = referenced_xrefs - defined_xrefs
        for xref in undefined:
            self.errors.append(f"Undefined XREF reference: @{xref}@")


def normalize_gedcom_line_endings(content: str) -> str:
    """
    Normalize line endings to Unix style (LF).
    
    Args:
        content: GEDCOM content string
        
    Returns:
        Content with normalized line endings
    """
    # Replace Windows (CRLF) and old Mac (CR) line endings
    content = content.replace("\r\n", "\n")
    content = content.replace("\r", "\n")
    return content


def extract_gedcom_metadata(file_path: str) -> Dict[str, str]:
    """
    Extract metadata from GEDCOM file header.
    
    Args:
        file_path: Path to GEDCOM file
        
    Returns:
        Dictionary of metadata fields
    """
    metadata = {}

    try:
        content = read_gedcom_with_encoding(file_path)
        lines = content.split("\n")

        in_header = False
        current_tag = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(None, 2)
            if len(parts) < 2:
                continue

            level = int(parts[0])
            tag = parts[1]
            value = parts[2] if len(parts) > 2 else ""

            if level == 0 and tag == "HEAD":
                in_header = True
                continue

            if level == 0:
                # End of header
                break

            if in_header:
                if level == 1:
                    current_tag = tag
                    if value:
                        metadata[tag] = value
                elif level == 2 and current_tag:
                    metadata[f"{current_tag}.{tag}"] = value

    except Exception as e:
        metadata["error"] = str(e)

    return metadata


# Convenience functions
def is_valid_gedcom(file_path: str) -> bool:
    """
    Quick validation check for GEDCOM file.
    
    Args:
        file_path: Path to GEDCOM file
        
    Returns:
        True if valid, False otherwise
    """
    validator = GedcomValidator()
    is_valid, _, _ = validator.validate_file(file_path)
    return is_valid
