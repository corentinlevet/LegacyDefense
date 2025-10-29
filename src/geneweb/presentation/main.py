import pathlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Importer le routeur web que nous venons de créer
from .web.routers import router as web_router

# Créer l'application FastAPI principale
app = FastAPI(
    title="GeneWeb Modernization",
    description="A modern Python-based version \
        of the GeneWeb genealogy software.",
    version="0.1.0",
)

# Définir le chemin vers le dossier des fichiers statiques
static_path = pathlib.Path(__file__).parent / "web" / "static"

# "Monter" le dossier statique pour qu'il soit accessible via l'URL "/static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Inclure le routeur web dans l'application principale
app.include_router(web_router)

# --- L'inclusion des routeurs de l'API se fera ici plus tard ---
# from .api.routers import persons_router
# app.include_router(persons_router, prefix="/api/v1")
