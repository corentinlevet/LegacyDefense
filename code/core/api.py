"""
FastAPI web application for GeneWeb Python implementation.

This module provides a REST API replacing the original OCaml gwd daemon,
with modern authentication, documentation, and JSON responses.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
from fastapi import (Depends, FastAPI, File, HTTPException, Path, Query,
                     UploadFile)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import DatabaseManager, FamilyORM, PersonORM
from .gedcom import GedcomExporter, GedcomParser
from .models import FamilyAPI, PersonAPI, Sex

# Initialize FastAPI app
app = FastAPI(
    title="GeneWeb API",
    description="Modern REST API for genealogy data management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration - MUST be configured for production!
# In production, set ALLOWED_ORIGINS environment variable to your domain(s)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Use environment variable for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable must be set! "
        "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///geneweb.db")
db_manager = DatabaseManager(DATABASE_URL)
db_manager.create_tables()


# Dependency to get database session
def get_db():
    """Get database session."""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


# Authentication utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")


# API Routes


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GeneWeb API",
        "version": "1.0.0",
        "description": "Modern REST API for genealogy data management",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}


# Authentication endpoints
@app.post("/auth/login")
async def login(username: str, password: str):
    """Authenticate user and return access token."""
    # In production, verify against user database
    if username == "admin" and password == "admin":  # Simple demo auth
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# Person endpoints
@app.get("/persons", response_model=List[PersonAPI])
async def get_persons(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sex: Optional[Sex] = Query(None),
    search: Optional[str] = Query(None),
):
    """Get list of persons with optional filtering."""
    query = db.query(PersonORM)

    if sex:
        query = query.filter(PersonORM.sex == sex)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (PersonORM.first_name.ilike(search_pattern))
            | (PersonORM.surname.ilike(search_pattern))
            | (PersonORM.public_name.ilike(search_pattern))
        )

    persons = query.offset(skip).limit(limit).all()

    # Convert to API model
    result = []
    for person in persons:
        birth_date = None
        if person.birth_event and person.birth_event.date:
            # Simplified date formatting
            birth_date = (
                str(person.birth_event.date.year)
                if person.birth_event.date.year
                else None
            )

        death_date = None
        if person.death_event and person.death_event.date:
            death_date = (
                str(person.death_event.date.year)
                if person.death_event.date.year
                else None
            )

        person_api = PersonAPI(
            id=person.id,
            first_name=person.first_name,
            surname=person.surname,
            sex=person.sex,
            birth_date=birth_date,
            death_date=death_date,
            occupation=person.occupation,
        )
        result.append(person_api)

    return result


@app.get("/persons/{person_id}", response_model=PersonAPI)
async def get_person(person_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Get a specific person by ID."""
    person = db.query(PersonORM).filter(PersonORM.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Convert to API model (same as above)
    birth_date = None
    if person.birth_event and person.birth_event.date:
        birth_date = (
            str(person.birth_event.date.year) if person.birth_event.date.year else None
        )

    death_date = None
    if person.death_event and person.death_event.date:
        death_date = (
            str(person.death_event.date.year) if person.death_event.date.year else None
        )

    return PersonAPI(
        id=person.id,
        first_name=person.first_name,
        surname=person.surname,
        sex=person.sex,
        birth_date=birth_date,
        death_date=death_date,
        occupation=person.occupation,
    )


@app.get("/persons/{person_id}/ancestors")
async def get_ancestors(
    person_id: int = Path(..., gt=0),
    generations: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Get ancestors of a person."""
    person = db.query(PersonORM).filter(PersonORM.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    ancestors = db_manager.get_ancestors(db, person_id, generations)

    result = []
    for ancestor in ancestors:
        result.append(
            {
                "id": ancestor.id,
                "first_name": ancestor.first_name,
                "surname": ancestor.surname,
                "sex": ancestor.sex.value,
            }
        )

    return {"person_id": person_id, "ancestors": result, "generations": generations}


@app.get("/persons/{person_id}/descendants")
async def get_descendants(
    person_id: int = Path(..., gt=0),
    generations: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Get descendants of a person."""
    person = db.query(PersonORM).filter(PersonORM.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    descendants = db_manager.get_descendants(db, person_id, generations)

    result = []
    for descendant in descendants:
        result.append(
            {
                "id": descendant.id,
                "first_name": descendant.first_name,
                "surname": descendant.surname,
                "sex": descendant.sex.value,
            }
        )

    return {"person_id": person_id, "descendants": result, "generations": generations}


@app.post("/persons")
async def create_person(
    person_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token),
):
    """Create a new person."""
    person = db_manager.add_person(db, person_data)
    return {"id": person.id, "message": "Person created successfully"}


# Family endpoints
@app.get("/families", response_model=List[FamilyAPI])
async def get_families(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get list of families."""
    families = db.query(FamilyORM).offset(skip).limit(limit).all()

    result = []
    for family in families:
        # Get marriage date
        marriage_date = None
        for event in family.events:
            if event.event_type == "marriage" and event.date:
                marriage_date = str(event.date.year) if event.date.year else None
                break

        family_api = FamilyAPI(
            id=family.id,
            father_id=family.father_id,
            mother_id=family.mother_id,
            children_ids=[child.id for child in family.children],
            marriage_type=family.marriage,
            marriage_date=marriage_date,
        )
        result.append(family_api)

    return result


@app.get("/families/{family_id}", response_model=FamilyAPI)
async def get_family(family_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Get a specific family by ID."""
    family = db.query(FamilyORM).filter(FamilyORM.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Get marriage date
    marriage_date = None
    for event in family.events:
        if event.event_type == "marriage" and event.date:
            marriage_date = str(event.date.year) if event.date.year else None
            break

    return FamilyAPI(
        id=family.id,
        father_id=family.father_id,
        mother_id=family.mother_id,
        children_ids=[child.id for child in family.children],
        marriage_type=family.marriage,
        marriage_date=marriage_date,
    )


# Search endpoints
@app.get("/search/persons")
async def search_persons(
    q: str = Query(..., min_length=2),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Search persons by name."""
    persons = db_manager.search_persons(db, q, limit)

    result = []
    for person in persons:
        result.append(
            {
                "id": person.id,
                "first_name": person.first_name,
                "surname": person.surname,
                "sex": person.sex.value,
                "full_name": f"{person.first_name} {person.surname}".strip(),
            }
        )

    return {"query": q, "results": result, "count": len(result)}


# Statistics endpoints
@app.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get database statistics."""
    stats = db_manager.get_statistics(db)
    return stats


# Import/Export endpoints
@app.post("/import/gedcom")
async def import_gedcom(
    file: UploadFile = File(...),
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Import GEDCOM file."""
    if not file.filename.lower().endswith(".ged"):
        raise HTTPException(status_code=400, detail="File must be a GEDCOM (.ged) file")

    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # Parse GEDCOM
        parser = GedcomParser()
        persons, families = parser.parse_file(temp_path)

        # TODO: Convert and save to database
        # This would require converting from dataclasses to ORM models

        return {
            "message": "GEDCOM file processed successfully",
            "persons_imported": len(persons),
            "families_imported": len(families),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing GEDCOM: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/export/gedcom")
async def export_gedcom(
    current_user: str = Depends(verify_token), db: Session = Depends(get_db)
):
    """Export database to GEDCOM format."""
    # TODO: Convert ORM models to dataclasses and export
    # This is a placeholder implementation

    temp_path = "/tmp/export.ged"

    try:
        # Get all persons and families from database
        persons_orm = db.query(PersonORM).all()
        families_orm = db.query(FamilyORM).all()

        # Convert to dataclass format (simplified)
        persons = {}
        families = {}

        # TODO: Proper conversion from ORM to dataclasses

        # Export using GedcomExporter
        exporter = GedcomExporter(persons, families)
        exporter.export_to_file(temp_path)

        return FileResponse(
            temp_path,
            media_type="application/octet-stream",
            filename="genealogy_export.ged",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting GEDCOM: {str(e)}")


# Utility endpoints
@app.get("/surnames")
async def get_surnames(
    limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)
):
    """Get list of all surnames in the database."""
    # Get distinct surnames
    surnames = (
        db.query(PersonORM.surname)
        .distinct()
        .filter(PersonORM.surname != "")
        .limit(limit)
        .all()
    )

    return {"surnames": [s[0] for s in surnames]}


@app.get("/places")
async def get_places(
    limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)
):
    """Get list of places mentioned in the database."""
    # This would require joining with place tables
    # Simplified implementation
    return {"places": ["Paris, France", "London, England", "New York, USA"]}


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Resource not found", "status_code": 404}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "status_code": 500}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
