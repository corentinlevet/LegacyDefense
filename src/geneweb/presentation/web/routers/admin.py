"""
Web UI routes for administration pages.
"""

import pathlib

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Chemin vers le dossier contenant les templates
templates_path = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

router = APIRouter()


@router.get(
    "/admin/errors-stats", response_class=HTMLResponse, name="errors_stats_page"
)
async def errors_stats_page(request: Request):
    """
    Serves the page displaying error history and statistics for administration.
    """
    return templates.TemplateResponse(
        "errors_stats.html",
        {
            "request": request,
        },
    )
