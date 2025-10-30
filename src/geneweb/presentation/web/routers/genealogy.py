"""
Web UI routes for genealogy-related pages.
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
    "/genealogies/create", response_class=HTMLResponse, name="create_genealogy_form"
)
async def create_genealogy_form(request: Request):
    """
    Serves the form page for creating a new genealogy.
    """
    return templates.TemplateResponse("create_genealogy.html", {"request": request})


@router.get("/genealogies", response_class=HTMLResponse, name="list_genealogies_page")
async def list_genealogies_page(request: Request):
    """
    Serves the page listing all available genealogies.
    """
    return templates.TemplateResponse("list_genealogies.html", {"request": request})


@router.get("/genealogy/{name}", response_class=HTMLResponse, name="view_genealogy")
async def view_genealogy(
    name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Serves the dashboard page for a specific genealogy,
    retrieving data via the service layer.
    """
    details = await app_service.get_genealogy_details(name)
    if not details:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "genealogy_dashboard.html",
        {
            "request": request,
            "genealogy_name": name,
            "nb_persons": details.person_count,
        },
    )


@router.get(
    "/genealogies/{genealogy_name}/import",
    response_class=HTMLResponse,
    name="import_gedcom_page",
)
async def import_gedcom_page(genealogy_name: str, request: Request):
    """
    Serves the page for importing a GEDCOM file into a specific genealogy.
    """
    return templates.TemplateResponse(
        "import_gedcom.html", {"request": request, "genealogy_name": genealogy_name}
    )


@router.get(
    "/genealogies/{genealogy_name}/export",
    response_class=HTMLResponse,
    name="export_gedcom_page",
)
async def export_gedcom_page(genealogy_name: str, request: Request):
    """
    Serves the page for exporting a GEDCOM file from a specific genealogy.
    """
    return templates.TemplateResponse(
        "export_gedcom.html", {"request": request, "genealogy_name": genealogy_name}
    )
