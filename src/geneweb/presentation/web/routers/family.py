"""
Web UI routes for family-related pages (add family, view family).
"""

import pathlib

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ....application.services import ApplicationService
from ...dependencies import get_app_service

# Chemin vers le dossier contenant les templates
templates_path = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

router = APIRouter()


# Placeholder for gettext function if not imported globally
def gettext(text: str) -> str:
    # This is a mock. Replace with your actual translation function.
    translations = {
        "Family Created": "Famille créée",
        "The family has been created successfully!": "La famille a été créée avec succès !",
        "Parents": "Parents",
        "Back to genealogy": "Retour à la généalogie",
    }
    return translations.get(text, text)


@router.get(
    "/genealogy/{genealogy_name}/add_family",
    response_class=HTMLResponse,
    name="add_family",
)
async def add_family_form(genealogy_name: str, request: Request):
    """
    Serves the form page for adding a new family to a genealogy.
    """
    return templates.TemplateResponse(
        "add_family.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "_": gettext,
        },
    )


@router.post("/genealogy/{genealogy_name}/add_family", name="add_family_post")
async def add_family_post(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Handles the submission of the add family form, creates a new family,
    and redirects to the family created page.
    """
    form_data = await request.form()
    family_id = await app_service.add_family(genealogy_name, form_data)
    return RedirectResponse(
        url=f"/genealogy/{genealogy_name}/family/{family_id}", status_code=303
    )


@router.get(
    "/genealogy/{genealogy_name}/family/{family_id}",
    response_class=HTMLResponse,
    name="family_created",
)
async def family_created(
    genealogy_name: str,
    family_id: int,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Serves the page confirming the creation of a family and displaying its details.
    """
    family = await app_service.get_family(family_id)
    return templates.TemplateResponse(
        "family_created.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "family": family,
            "_": gettext,
        },
    )
