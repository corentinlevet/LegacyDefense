"""
Web UI routes for base pages like home, genealogy selection, and admin setup.
"""

import pathlib

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Chemin vers le dossier contenant les templates
templates_path = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="read_start_page")
async def read_start_page(request: Request):
    """
    Serves the application's start page.
    """
    context = {"request": request}
    return templates.TemplateResponse("start.html", context)


@router.get("/gwd", response_class=HTMLResponse, name="read_select_page")
async def read_select_page(request: Request):
    """
    Serves the genealogy tree selection page.
    """
    context = {"request": request}
    return templates.TemplateResponse("gwd.html", context)


@router.get("/gwsetup", response_class=HTMLResponse, name="read_admin_page")
async def read_admin_page(request: Request):
    """
    Serves the management and creation page.
    """
    context = {"request": request}
    return templates.TemplateResponse("gwsetup.html", context)
