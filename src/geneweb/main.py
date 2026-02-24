import asyncio
import pathlib
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .infrastructure import config_models  # noqa: F401 – registers models
from .infrastructure import models  # noqa: F401 – registers models
from .infrastructure.database import Base, engine
from .presentation.api.routers import api_router
from .presentation.web.routers import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all database tables on startup if they don't exist yet
    Base.metadata.create_all(bind=engine)
    yield


# Créer l'application FastAPI principale
app = FastAPI(
    title="GeneWeb Modernization",
    description="A modern Python-based version \
        of the GeneWeb genealogy software.",
    version="0.1.0",
    lifespan=lifespan,
)

# Définir le chemin vers le dossier des fichiers statiques
static_path = pathlib.Path(__file__).parent / "presentation" / "web" / "static"

# "Monter" le dossier statique pour qu'il soit accessible via l'URL "/static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

app.include_router(web_router)
app.include_router(api_router)
