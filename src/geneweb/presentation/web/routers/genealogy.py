"""
Web UI routes for genealogy-related pages.
"""

import os
import pathlib
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ....application.services import ApplicationService
from ....infrastructure.geneweb_parser import GeneWebExporter, GeneWebParser
from ...dependencies import get_app_service, get_db

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


@router.get(
    "/genealogy/{genealogy_name}/manage",
    response_class=HTMLResponse,
    name="manage_genealogy_page",
)
async def manage_genealogy_page(genealogy_name: str, request: Request):
    """
    Serves the page for managing (renaming/deleting) a specific genealogy.
    """
    return templates.TemplateResponse(
        "manage_genealogy.html", {"request": request, "genealogy_name": genealogy_name}
    )


@router.post(
    "/genealogy/{genealogy_name}/rename",
    response_class=HTMLResponse,
    name="rename_genealogy",
)
async def rename_genealogy(
    genealogy_name: str,
    request: Request,
    new_name: str = Form(...),
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Handles the renaming of a genealogy.
    """
    genealogy = await app_service.rename_genealogy(genealogy_name, new_name)
    if not genealogy:
        raise HTTPException(status_code=404, detail="Genealogy not found")
    return templates.TemplateResponse(
        "genealogy_dashboard.html",
        {
            "request": request,
            "genealogy_name": genealogy.name,
            "nb_persons": genealogy.person_count,
            "message": f"Genealogy renamed to {genealogy.name} successfully!",
        },
    )


@router.post(
    "/genealogy/{genealogy_name}/delete",
    response_class=HTMLResponse,
    name="delete_genealogy",
)
async def delete_genealogy(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Handles the deletion of a genealogy.
    """
    success = await app_service.delete_genealogy(genealogy_name)
    if not success:
        raise HTTPException(status_code=404, detail="Genealogy not found")
    return templates.TemplateResponse(
        "list_genealogies.html",
        {
            "request": request,
            "message": f"Genealogy {genealogy_name} deleted successfully!",
        },
    )


@router.get(
    "/genealogy/{genealogy_name}/advanced_options",
    response_class=HTMLResponse,
    name="advanced_genealogy_options_page",
)
async def advanced_genealogy_options_page(genealogy_name: str, request: Request):
    """
    Serves the page for advanced options of a specific genealogy.
    """
    return templates.TemplateResponse(
        "advanced_genealogy_options.html",
        {"request": request, "genealogy_name": genealogy_name},
    )


@router.get(
    "/genealogies/import-geneweb",
    response_class=HTMLResponse,
    name="import_geneweb_page",
)
async def import_geneweb_page(request: Request):
    """
    Serves the page for importing a GeneWeb file.
    """
    return templates.TemplateResponse("import_geneweb.html", {"request": request})


@router.post("/genealogies/import-geneweb", name="import_geneweb_route")
async def import_geneweb_route(
    request: Request,
    base_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Import a GeneWeb (.gw) file directly into the database.
    """
    try:
        # Read the uploaded file
        gw_content = await file.read()
        gw_text = gw_content.decode("utf-8")

        # Create the genealogy if it doesn't exist
        from ....infrastructure.models import Genealogy

        existing_genealogy = (
            db.query(Genealogy).filter(Genealogy.name == base_name).first()
        )

        if not existing_genealogy:
            new_genealogy = Genealogy(name=base_name)
            db.add(new_genealogy)
            db.commit()
            db.refresh(new_genealogy)
            genealogy = new_genealogy
        else:
            genealogy = existing_genealogy

        # Parse GeneWeb format and import directly to database
        parser = GeneWebParser()
        parser.import_to_db(gw_text, genealogy.id, db)

        db.commit()

        return RedirectResponse(url=f"/genealogy/{base_name}", status_code=303)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error importing GeneWeb file: {str(e)}"
        )


@router.get(
    "/genealogies/{genealogy_name}/export-geneweb",
    response_class=StreamingResponse,
    name="export_geneweb",
)
async def export_geneweb(genealogy_name: str, db: Session = Depends(get_db)):
    """
    Exports a genealogy to a GeneWeb file and returns it for download.
    """
    tmp_file_path = None
    try:
        # Create exporter and generate GeneWeb content
        exporter = GeneWebExporter(db, genealogy_name)
        gw_content = exporter.export()

        # Save to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".gw", encoding="utf-8"
        ) as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(gw_content)

        # Stream the file response
        def file_iterator(file_path):
            with open(file_path, "rb") as f:
                yield from f
            os.unlink(file_path)

        return StreamingResponse(
            file_iterator(tmp_file_path),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={genealogy_name}.gw"
            },
        )

    except Exception as e:
        print(f"An exception of type {type(e).__name__} occurred: {e}")
        import traceback

        traceback.print_exc()
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(
            status_code=500, detail=f"Error exporting GeneWeb file: {str(e)}"
        )
