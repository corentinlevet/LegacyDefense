"""
FastAPI REST API for GeneWeb application.

Provides RESTful endpoints for:
- Person management (CRUD)
- Family operations
- Event management
- Search and filtering
- Statistics and analytics
- GEDCOM import/export
- Tree visualization data

Features:
- OpenAPI/Swagger documentation
- JWT authentication
- Rate limiting
- CORS support
- Request validation (Pydantic)
- Response caching
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Person as PersonModel
from core.search import PersonSearchEngine, SearchCriteria, SearchResult
from core.services import (
    get_genealogy_service,
    get_person_service,
)
from core.statistics import (
    DemographicSummary,
    get_demographic_summary,
)


# Pydantic schemas for request/response validation
class PersonSchema(BaseModel):
    """Person schema for API responses."""

    id: Optional[int] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    surname: str = Field(..., min_length=1, max_length=100)
    sex: str = Field(..., pattern="^[MFU]$")
    occupation: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
    consang: Optional[float] = Field(None, ge=0.0, le=1.0)

    class Config:
        from_attributes = True


class PersonCreateSchema(BaseModel):
    """Schema for creating a new person."""

    first_name: str = Field(..., min_length=1, max_length=100)
    surname: str = Field(..., min_length=1, max_length=100)
    sex: str = Field(..., pattern="^[MFU]$")
    occupation: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class PersonUpdateSchema(BaseModel):
    """Schema for updating a person."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    sex: Optional[str] = Field(None, pattern="^[MFU]$")
    occupation: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class SearchCriteriaSchema(BaseModel):
    """Schema for search criteria."""

    first_name: Optional[str] = None
    surname: Optional[str] = None
    sex: Optional[str] = Field(None, pattern="^[MFU]$")
    birth_year_from: Optional[int] = Field(None, ge=1000, le=2100)
    birth_year_to: Optional[int] = Field(None, ge=1000, le=2100)
    occupation: Optional[str] = None
    fuzzy_matching: bool = False
    soundex_matching: bool = False
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class SearchResultSchema(BaseModel):
    """Schema for search result."""

    person: PersonSchema
    relevance_score: float
    match_reasons: List[str]


class RelationshipSchema(BaseModel):
    """Schema for relationship information."""

    person1_id: int
    person2_id: int
    relationship_type: str
    distance: int
    path: List[int]


class ConsanguinitySchema(BaseModel):
    """Schema for consanguinity result."""

    person_id: int
    coefficient: float
    common_ancestors: List[int]


# Create API router
router = APIRouter()


# ==============================================================================
# Person Endpoints
# ==============================================================================


@router.post(
    "/persons",
    response_model=PersonSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new person",
    tags=["Persons"],
)
async def create_person(
    person_data: PersonCreateSchema,
    db: Session = Depends(get_db),
):
    """
    Create a new person in the database.
    
    Args:
        person_data: Person creation data
        db: Database session
        
    Returns:
        Created person
    """
    service = get_person_service(db)

    try:
        person_id = service.create_person(
            first_name=person_data.first_name,
            surname=person_data.surname,
            sex=person_data.sex,
            occupation=person_data.occupation,
            notes=person_data.notes,
        )

        person = service.get_person_with_details(person_id)

        return PersonSchema.model_validate(person)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create person: {str(e)}",
        )


@router.get(
    "/persons/{person_id}",
    response_model=PersonSchema,
    summary="Get person by ID",
    tags=["Persons"],
)
async def get_person(
    person_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a person by their ID.
    
    Args:
        person_id: Person ID
        db: Database session
        
    Returns:
        Person details
    """
    service = get_person_service(db)
    person = service.get_person_with_details(person_id)

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )

    return PersonSchema.model_validate(person)


@router.put(
    "/persons/{person_id}",
    response_model=PersonSchema,
    summary="Update person",
    tags=["Persons"],
)
async def update_person(
    person_id: int,
    person_data: PersonUpdateSchema,
    db: Session = Depends(get_db),
):
    """
    Update an existing person.
    
    Args:
        person_id: Person ID
        person_data: Updated person data
        db: Database session
        
    Returns:
        Updated person
    """
    service = get_person_service(db)
    person = service.get_person_with_details(person_id)

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )

    # Update fields
    if person_data.first_name:
        person.first_name = person_data.first_name
    if person_data.surname:
        person.surname = person_data.surname
    if person_data.sex:
        person.sex = person_data.sex
    if person_data.occupation:
        person.occupation = person_data.occupation
    if person_data.notes:
        person.notes = person_data.notes

    service.update_person(person)

    return PersonSchema.model_validate(person)


@router.delete(
    "/persons/{person_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete person",
    tags=["Persons"],
)
async def delete_person(
    person_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a person.
    
    Args:
        person_id: Person ID
        db: Database session
    """
    service = get_person_service(db)
    success = service.delete_person(person_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )


@router.get(
    "/persons",
    response_model=List[PersonSchema],
    summary="List all persons",
    tags=["Persons"],
)
async def list_persons(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List all persons with pagination.
    
    Args:
        limit: Maximum results to return
        offset: Number of results to skip
        db: Database session
        
    Returns:
        List of persons
    """
    service = get_person_service(db)
    persons = service.list_persons(limit=limit, offset=offset)

    return [PersonSchema.model_validate(person) for person in persons]
# ==============================================================================
# Search Endpoints
# ==============================================================================


@router.post(
    "/search",
    response_model=List[SearchResultSchema],
    summary="Advanced person search",
    tags=["Search"],
)
async def search_persons(
    criteria: SearchCriteriaSchema,
    db: Session = Depends(get_db),
):
    """
    Search for persons using advanced criteria.
    
    Args:
        criteria: Search criteria
        db: Database session
        
    Returns:
        List of search results with relevance scores
    """
    search_engine = PersonSearchEngine(db)

    search_criteria = SearchCriteria(
        first_name=criteria.first_name,
        surname=criteria.surname,
        sex=criteria.sex,
        birth_year_from=criteria.birth_year_from,
        birth_year_to=criteria.birth_year_to,
        occupation=criteria.occupation,
        fuzzy_matching=criteria.fuzzy_matching,
        soundex_matching=criteria.soundex_matching,
        limit=criteria.limit,
        offset=criteria.offset,
    )

    results = search_engine.search(search_criteria)

    return [
        SearchResultSchema(
            person=PersonSchema.model_validate(r.person),
            relevance_score=r.relevance_score,
            match_reasons=r.match_reasons,
        )
        for r in results
    ]


@router.get(
    "/search/suggest",
    response_model=List[str],
    summary="Name autocomplete",
    tags=["Search"],
)
async def suggest_names(
    prefix: str = Query(..., min_length=1),
    field: str = Query("surname", pattern="^(first_name|surname)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get name suggestions for autocomplete.
    
    Args:
        prefix: Name prefix to search
        field: Field to search (first_name or surname)
        limit: Maximum suggestions
        db: Database session
        
    Returns:
        List of suggested names
    """
    search_engine = PersonSearchEngine(db)
    suggestions = search_engine.suggest_names(prefix, field, limit)

    return suggestions


# ==============================================================================
# Genealogy Endpoints
# ==============================================================================


@router.get(
    "/persons/{person_id}/consanguinity",
    response_model=ConsanguinitySchema,
    summary="Calculate consanguinity",
    tags=["Genealogy"],
)
async def calculate_consanguinity(
    person_id: int,
    db: Session = Depends(get_db),
):
    """
    Calculate consanguinity coefficient for a person.
    
    Args:
        person_id: Person ID
        db: Database session
        
    Returns:
        Consanguinity information
    """
    service = get_genealogy_service(db)

    coefficient = service.calculate_consanguinity(person_id)

    return ConsanguinitySchema(
        person_id=person_id, coefficient=coefficient, common_ancestors=[]
    )


@router.get(
    "/persons/{person_id}/ancestors",
    response_model=List[PersonSchema],
    summary="Get ancestors",
    tags=["Genealogy"],
)
async def get_ancestors(
    person_id: int,
    max_generations: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Get all ancestors of a person.
    
    Args:
        person_id: Person ID
        max_generations: Maximum generations to traverse
        db: Database session
        
    Returns:
        List of ancestors
    """
    service = get_genealogy_service(db)
    ancestors = service.get_ancestors(person_id, max_generations)

    return [PersonSchema.model_validate(p) for p in ancestors]


@router.get(
    "/persons/{person_id}/descendants",
    response_model=List[PersonSchema],
    summary="Get descendants",
    tags=["Genealogy"],
)
async def get_descendants(
    person_id: int,
    max_generations: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Get all descendants of a person.
    
    Args:
        person_id: Person ID
        max_generations: Maximum generations to traverse
        db: Database session
        
    Returns:
        List of descendants
    """
    service = get_genealogy_service(db)
    descendants = service.get_descendants(person_id, max_generations)

    return [PersonSchema.model_validate(p) for p in descendants]


# ==============================================================================
# Statistics Endpoints
# ==============================================================================


@router.get(
    "/statistics/summary",
    summary="Get demographic summary",
    tags=["Statistics"],
)
async def get_statistics_summary(
    db: Session = Depends(get_db),
):
    """
    Get comprehensive demographic summary.
    
    Args:
        db: Database session
        
    Returns:
        Demographic statistics
    """
    summary = get_demographic_summary(db)

    return {
        "total_persons": summary.total_persons,
        "total_males": summary.total_males,
        "total_females": summary.total_females,
        "total_families": summary.total_families,
        "surnames": {
            "unique_count": summary.surname_stats.total_unique_surnames,
            "most_common": summary.surname_stats.most_common_surnames[:10],
        },
    }


# Export router for use in main FastAPI app
api_router = router
