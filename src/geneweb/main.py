import pathlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .presentation.api.routers import api_router
from .presentation.web.routers import router as web_router

# Créer l'application FastAPI principale
app = FastAPI(
    title="GeneWeb Modernization",
    description="A modern Python-based version \
        of the GeneWeb genealogy software.",
    version="0.1.0",
)

# Définir le chemin vers le dossier des fichiers statiques
static_path = pathlib.Path(__file__).parent / "presentation" / "web" / "static"

# "Monter" le dossier statique pour qu'il soit accessible via l'URL "/static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

app.include_router(web_router)
app.include_router(api_router)
