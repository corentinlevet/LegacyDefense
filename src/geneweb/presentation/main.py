import pathlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Import des nouveaux routers pour la configuration
from .api.config_api import router as config_api_router
from .api.routers import router as api_router
from .web.config_routers import router as config_web_router
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

app.include_router(web_router)
app.include_router(api_router)
# Ajout des nouveaux routers de configuration
app.include_router(config_web_router)
app.include_router(config_api_router)
