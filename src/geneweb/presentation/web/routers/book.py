"""
Web UI routes for "book" pages (lists of first names, last names, places, etc.).
"""

import pathlib

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ....application.services import ApplicationService
from ...dependencies import get_app_service

# Chemin vers le dossier contenant les templates
templates_path = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

router = APIRouter()


@router.get(
    "/genealogy/{genealogy_name}/book/first_names",
    response_class=HTMLResponse,
    name="book_first_names",
)
async def book_first_names(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Displays the book of first names for a genealogy.
    """
    first_names = await app_service.get_first_names(genealogy_name)
    if first_names is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_first_names.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "first_names": first_names,
        },
    )


@router.get(
    "/genealogy/{genealogy_name}/book/last_names",
    response_class=HTMLResponse,
    name="book_last_names",
)
async def book_last_names(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Displays the book of last names for a genealogy.
    """
    last_names = await app_service.get_last_names(genealogy_name)
    if last_names is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_last_names.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "last_names": last_names,
        },
    )


@router.get(
    "/genealogy/{genealogy_name}/book/places",
    response_class=HTMLResponse,
    name="book_places",
)
async def book_places(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Displays the book of places for a genealogy.
    """
    places = await app_service.get_places(genealogy_name)
    if places is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_places.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "places": places,
        },
    )


@router.get(
    "/genealogy/{genealogy_name}/book/occupations",
    response_class=HTMLResponse,
    name="book_occupations",
)
async def book_occupations(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Displays the book of occupations for a genealogy.
    """
    occupations = await app_service.get_occupations(genealogy_name)
    if occupations is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_occupations.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "occupations": occupations,
        },
    )


@router.get(
    "/genealogy/{genealogy_name}/book/sources",
    response_class=HTMLResponse,
    name="book_sources",
)
async def book_sources(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Displays the book of sources for a genealogy.
    """
    sources = await app_service.get_sources(genealogy_name)
    if sources is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_sources.html",
        {"request": request, "genealogy_name": genealogy_name, "sources": sources},
    )
