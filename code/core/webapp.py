"""
Web interface for GeneWeb Python implementation.

This module creates a complete web application using the templates
and provides the same user experience as the original OCaml version.
"""
from fastapi import FastAPI, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn
import os

from .database import DatabaseManager, PersonORM, FamilyORM, EventORM, DateORM
from .templates import TemplateEnvironment, initialize_templates
from .algorithms import GenealogyAlgorithms
from .gedcom import GedcomParser, GedcomExporter
from .models import Sex


class GeneWebApp:
    """Main GeneWeb web application."""
    
    def __init__(self, db_url: str = "sqlite:///geneweb.db"):
        """Initialize the web application."""
        self.app = FastAPI(
            title="GeneWeb",
            description="Modern genealogy application",
            version="1.0.0"
        )
        
        # Database setup
        self.db_manager = DatabaseManager(db_url)
        self.db_manager.create_tables()
        
        # Template setup
        self.template_env = initialize_templates("templates", "locales")
        
        # Algorithms
        self.algorithms = GenealogyAlgorithms(self.db_manager)
        
        # Static files
        os.makedirs("static", exist_ok=True)
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        # Setup routes
        self._setup_routes()
    
    def get_db(self):
        """Database dependency."""
        session = self.db_manager.get_session()
        try:
            yield session
        finally:
            session.close()
    
    def _setup_routes(self):
        """Setup all application routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request, db: Session = Depends(self.get_db)):
            """Home page."""
            # Get some statistics for the home page
            total_persons = db.query(PersonORM).count()
            total_families = db.query(FamilyORM).count()
            
            # Get recent additions (last 10 persons)
            recent_persons = db.query(PersonORM).order_by(PersonORM.id.desc()).limit(10).all()
            
            context = {
                "request": request,
                "total_persons": total_persons,
                "total_families": total_families,
                "recent_persons": recent_persons
            }
            
            return HTMLResponse(self.template_env.render_template("home.html", **context))
        
        @self.app.get("/persons", response_class=HTMLResponse)
        async def persons_list(
            request: Request, 
            page: int = 1, 
            search: str = "", 
            db: Session = Depends(self.get_db)
        ):
            """List all persons with pagination."""
            per_page = 50
            offset = (page - 1) * per_page
            
            query = db.query(PersonORM)
            
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (PersonORM.first_name.ilike(search_pattern)) |
                    (PersonORM.surname.ilike(search_pattern))
                )
            
            total_count = query.count()
            persons = query.offset(offset).limit(per_page).all()
            
            total_pages = (total_count + per_page - 1) // per_page
            
            context = {
                "request": request,
                "persons": persons,
                "current_page": page,
                "total_pages": total_pages,
                "search": search,
                "total_count": total_count
            }
            
            return HTMLResponse(self.template_env.render_template("persons.html", **context))
        
        @self.app.get("/persons/{person_id}", response_class=HTMLResponse)
        async def person_detail(
            request: Request, 
            person_id: int, 
            db: Session = Depends(self.get_db)
        ):
            """Person detail page."""
            person = db.query(PersonORM).filter(PersonORM.id == person_id).first()
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")
            
            # Get family information
            parents = None
            if person.parent_family:
                parents = {
                    'father': person.parent_family.father,
                    'mother': person.parent_family.mother
                }
            
            # Get spouse families
            spouses = []
            spouse_families = db.query(FamilyORM).filter(
                (FamilyORM.father_id == person_id) | (FamilyORM.mother_id == person_id)
            ).all()
            
            for family in spouse_families:
                spouse = family.mother if family.father_id == person_id else family.father
                if spouse:
                    spouses.append({
                        'spouse': spouse,
                        'marriage_date': None,  # TODO: Get from family events
                        'family': family
                    })
            
            # Get children
            children = []
            for family in spouse_families:
                family_children = db.query(PersonORM).filter(
                    PersonORM.parent_family_id == family.id
                ).all()
                children.extend(family_children)
            
            context = {
                "request": request,
                "person": person,
                "parents": parents,
                "spouses": spouses,
                "children": children
            }
            
            return HTMLResponse(self.template_env.render_template("person_detail.html", **context))
        
        # Alternative route for backwards compatibility (person/ instead of persons/)
        @self.app.get("/person/{person_id}", response_class=HTMLResponse)
        async def person_detail_alt(
            request: Request, 
            person_id: int, 
            db: Session = Depends(self.get_db)
        ):
            """Person detail page (alternative route)."""
            return await person_detail(request, person_id, db)
        
        @self.app.get("/persons/{person_id}/ancestors", response_class=HTMLResponse)
        async def person_ancestors(
            request: Request, 
            person_id: int, 
            generations: int = 5,
            db: Session = Depends(self.get_db)
        ):
            """Show person's ancestors."""
            person = db.query(PersonORM).filter(PersonORM.id == person_id).first()
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")
            
            # Get ancestors
            ancestor_ids = self.algorithms.get_ancestors(db, person_id, generations)
            ancestors = db.query(PersonORM).filter(PersonORM.id.in_(ancestor_ids)).all()
            
            # Organize by generation (simplified)
            ancestors_by_gen = {}
            for ancestor in ancestors:
                # TODO: Calculate actual generation
                gen = 1  # Placeholder
                if gen not in ancestors_by_gen:
                    ancestors_by_gen[gen] = []
                ancestors_by_gen[gen].append(ancestor)
            
            context = {
                "request": request,
                "person": person,
                "ancestors_by_generation": ancestors_by_gen,
                "generations": generations
            }
            
            return HTMLResponse(self.template_env.render_template("ancestors.html", **context))
        
        @self.app.get("/persons/{person_id}/descendants", response_class=HTMLResponse)
        async def person_descendants(
            request: Request, 
            person_id: int, 
            generations: int = 5,
            db: Session = Depends(self.get_db)
        ):
            """Show person's descendants."""
            person = db.query(PersonORM).filter(PersonORM.id == person_id).first()
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")
            
            # Get descendants
            descendant_ids = self.algorithms.get_descendants(db, person_id, generations)
            descendants = db.query(PersonORM).filter(PersonORM.id.in_(descendant_ids)).all()
            
            context = {
                "request": request,
                "person": person,
                "descendants": descendants,
                "generations": generations
            }
            
            return HTMLResponse(self.template_env.render_template("descendants.html", **context))
        
        @self.app.get("/families", response_class=HTMLResponse)
        async def families_list(
            request: Request, 
            page: int = 1, 
            db: Session = Depends(self.get_db)
        ):
            """List all families."""
            per_page = 20
            offset = (page - 1) * per_page
            
            families = db.query(FamilyORM).offset(offset).limit(per_page).all()
            total_count = db.query(FamilyORM).count()
            total_pages = (total_count + per_page - 1) // per_page
            
            context = {
                "request": request,
                "families": families,
                "current_page": page,
                "total_pages": total_pages
            }
            
            return HTMLResponse(self.template_env.render_template("family_list.html", **context))
        
        @self.app.get("/search", response_class=HTMLResponse)
        async def search_page(
            request: Request, 
            q: str = "", 
            db: Session = Depends(self.get_db)
        ):
            """Search page."""
            results = []
            
            if q:
                # Search persons
                search_pattern = f"%{q}%"
                results = db.query(PersonORM).filter(
                    (PersonORM.first_name.ilike(search_pattern)) |
                    (PersonORM.surname.ilike(search_pattern)) |
                    (PersonORM.public_name.ilike(search_pattern))
                ).limit(100).all()
            
            context = {
                "request": request,
                "query": q,
                "results": results
            }
            
            return HTMLResponse(self.template_env.render_template("search.html", **context))
        
        @self.app.get("/statistics", response_class=HTMLResponse)
        async def statistics(request: Request, db: Session = Depends(self.get_db)):
            """Statistics page."""
            stats = self.algorithms.get_statistics(db)
            
            # Get additional statistics
            stats.update({
                'oldest_person': db.query(PersonORM)\
                    .join(EventORM, PersonORM.birth_event)\
                    .join(DateORM, EventORM.date)\
                    .filter(DateORM.year != None)\
                    .order_by(DateORM.year.asc())\
                    .first(),
                'most_children': None,  # TODO: Calculate
                'most_common_surnames': [],  # TODO: Calculate
            })
            
            context = {
                "request": request,
                "stats": stats
            }
            
            return HTMLResponse(self.template_env.render_template("statistics.html", **context))
        
        @self.app.get("/import", response_class=HTMLResponse)
        async def import_page(request: Request):
            """Import page."""
            context = {"request": request}
            return HTMLResponse(self.template_env.render_template("import.html", **context))
        
        @self.app.post("/import/gedcom")
        async def import_gedcom(
            request: Request,
            file: UploadFile = File(...),
            db: Session = Depends(self.get_db)
        ):
            """Import GEDCOM file."""
            if not file.filename.lower().endswith('.ged'):
                context = {
                    "request": request,
                    "error": "File must be a GEDCOM (.ged) file"
                }
                return HTMLResponse(self.template_env.render_template("import.html", **context))
            
            # Save uploaded file temporarily
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            try:
                # Parse GEDCOM
                parser = GedcomParser()
                persons, families = parser.parse_file(temp_path)
                
                # TODO: Save to database
                # This requires converting dataclass models to ORM models
                
                context = {
                    "request": request,
                    "success": f"Successfully imported {len(persons)} persons and {len(families)} families"
                }
                
            except Exception as e:
                context = {
                    "request": request,
                    "error": f"Error importing GEDCOM: {str(e)}"
                }
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return HTMLResponse(self.template_env.render_template("import.html", **context))
        
        @self.app.get("/export/gedcom")
        async def export_gedcom(db: Session = Depends(self.get_db)):
            """Export database to GEDCOM."""
            # TODO: Convert ORM models to dataclass models and export
            # This is a placeholder
            temp_path = "/tmp/export.ged"
            
            try:
                # Get all data
                persons_orm = db.query(PersonORM).all()
                families_orm = db.query(FamilyORM).all()
                
                # TODO: Convert to dataclass format for export
                persons = {}
                families = {}
                
                # Export
                exporter = GedcomExporter(persons, families)
                exporter.export_to_file(temp_path)
                
                # Return file
                from fastapi.responses import FileResponse
                return FileResponse(
                    temp_path,
                    media_type="application/octet-stream",
                    filename="genealogy_export.ged"
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
        
        @self.app.get("/admin", response_class=HTMLResponse)
        async def admin_page(request: Request, db: Session = Depends(self.get_db)):
            """Admin page."""
            stats = self.algorithms.get_statistics(db)
            
            # Get data consistency issues
            inconsistencies = self.algorithms.detect_data_inconsistencies(db)
            
            context = {
                "request": request,
                "stats": stats,
                "inconsistencies": inconsistencies
            }
            
            return HTMLResponse(self.template_env.render_template("admin.html", **context))
        
        @self.app.post("/admin/compute-consanguinity")
        async def compute_consanguinity(request: Request, db: Session = Depends(self.get_db)):
            """Compute consanguinity for all persons."""
            try:
                results = self.algorithms.compute_all_consanguinity(db, from_scratch=True)
                
                context = {
                    "request": request,
                    "success": f"Computed consanguinity for {len(results)} persons",
                    "stats": self.algorithms.get_statistics(db),
                    "inconsistencies": []
                }
                
            except Exception as e:
                context = {
                    "request": request,
                    "error": f"Error computing consanguinity: {str(e)}",
                    "stats": {},
                    "inconsistencies": []
                }
            
            return HTMLResponse(self.template_env.render_template("admin.html", **context))
        
        @self.app.get("/surnames", response_class=HTMLResponse)
        async def surnames_list(request: Request, db: Session = Depends(self.get_db)):
            """List all surnames."""
            # Get surnames with person counts
            surnames = db.query(PersonORM.surname).filter(
                PersonORM.surname != ""
            ).distinct().all()
            
            surname_counts = []
            for (surname,) in surnames:
                count = db.query(PersonORM).filter(PersonORM.surname == surname).count()
                surname_counts.append((surname, count))
            
            # Sort by count descending
            surname_counts.sort(key=lambda x: x[1], reverse=True)
            
            context = {
                "request": request,
                "surname_counts": surname_counts
            }
            
            return HTMLResponse(self.template_env.render_template("surnames.html", **context))
        
        @self.app.get("/surnames/{surname}", response_class=HTMLResponse)
        async def surname_detail(
            request: Request, 
            surname: str, 
            db: Session = Depends(self.get_db)
        ):
            """Show all persons with a specific surname."""
            persons = db.query(PersonORM).filter(PersonORM.surname == surname).all()
            
            context = {
                "request": request,
                "surname": surname,
                "persons": persons
            }
            
            return HTMLResponse(self.template_env.render_template("surname_detail.html", **context))
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Run the web application."""
        uvicorn.run(self.app, host=host, port=port, reload=debug)


# Create additional templates that are missing
ADDITIONAL_TEMPLATES = {
    "home.html": """
<!DOCTYPE html>
<html lang="{{ current_lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ _('genealogy') }} - {{ _('home') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
        .header h1 { margin: 0; }
        .nav { margin: 20px 0; }
        .nav a { color: #3498db; text-decoration: none; margin-right: 20px; }
        .nav a:hover { text-decoration: underline; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex: 1; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .recent-persons { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ _('genealogy') }}</h1>
        <p>{{ _('welcome_message') }}</p>
    </div>
    
    <div class="nav">
        <a href="{{ url_for('persons_list') }}">{{ _('persons') }}</a>
        <a href="{{ url_for('families_list') }}">{{ _('families') }}</a>
        <a href="{{ url_for('search_page') }}">{{ _('search') }}</a>
        <a href="{{ url_for('surnames_list') }}">{{ _('surnames') }}</a>
        <a href="{{ url_for('statistics') }}">{{ _('statistics') }}</a>
        <a href="{{ url_for('import_page') }}">{{ _('import') }}</a>
        <a href="{{ url_for('admin_page') }}">{{ _('admin') }}</a>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{{ total_persons|format_number }}</div>
            <div>{{ _('persons') }}</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ total_families|format_number }}</div>
            <div>{{ _('families') }}</div>
        </div>
    </div>
    
    {% if recent_persons %}
    <div class="recent-persons">
        <h3>{{ _('recent_additions') }}</h3>
        <ul>
            {% for person in recent_persons %}
            <li>
                <a href="{{ url_for('person_detail', person_id=person.id) }}">
                    {{ person.first_name }} {{ person.surname }}
                </a>
            </li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}
</body>
</html>
    """,
    
    "persons_list.html": """
<!DOCTYPE html>
<html lang="{{ current_lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ _('persons') }} - {{ _('genealogy') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .search-box { margin: 20px 0; }
        .search-box input { padding: 8px; width: 300px; margin-right: 10px; }
        .search-box button { padding: 8px 15px; }
        .person-list { list-style: none; padding: 0; }
        .person-item { border: 1px solid #ddd; margin: 5px 0; padding: 10px; border-radius: 3px; }
        .person-name { font-weight: bold; }
        .person-details { color: #666; margin-top: 5px; }
        .pagination { margin: 20px 0; text-align: center; }
        .pagination a { margin: 0 5px; padding: 5px 10px; text-decoration: none; border: 1px solid #ddd; }
        .pagination .current { background: #007bff; color: white; }
    </style>
</head>
<body>
    <h1>{{ _('persons') }} ({{ total_count }})</h1>
    
    <div class="search-box">
        <form method="GET">
            <input type="text" name="search" value="{{ search }}" placeholder="{{ _('search_names') }}">
            <button type="submit">{{ _('search') }}</button>
            {% if search %}<a href="{{ url_for('persons_list') }}">{{ _('clear') }}</a>{% endif %}
        </form>
    </div>
    
    <ul class="person-list">
        {% for person in persons %}
        <li class="person-item">
            <div class="person-name">
                <a href="{{ url_for('person_detail', person_id=person.id) }}">
                    {{ person.first_name }} {{ person.surname }}
                </a>
                <span>{{ person.sex|sex_symbol }}</span>
            </div>
            <div class="person-details">
                {% if person.birth_date %}{{ _('born') }}: {{ person.birth_date }}{% endif %}
                {% if person.occupation %} | {{ person.occupation }}{% endif %}
            </div>
        </li>
        {% endfor %}
    </ul>
    
    {% if total_pages > 1 %}
    <div class="pagination">
        {% if current_page > 1 %}
            <a href="?page={{ current_page - 1 }}{% if search %}&search={{ search }}{% endif %}">&laquo; {{ _('previous') }}</a>
        {% endif %}
        
        {% for page_num in range(1, total_pages + 1) %}
            {% if page_num == current_page %}
                <span class="current">{{ page_num }}</span>
            {% else %}
                <a href="?page={{ page_num }}{% if search %}&search={{ search }}{% endif %}">{{ page_num }}</a>
            {% endif %}
        {% endfor %}
        
        {% if current_page < total_pages %}
            <a href="?page={{ current_page + 1 }}{% if search %}&search={{ search }}{% endif %}">{{ _('next') }} &raquo;</a>
        {% endif %}
    </div>
    {% endif %}
    
    <div>
        <a href="{{ url_for('home') }}">{{ _('home') }}</a>
    </div>
</body>
</html>
    """
}


# Entry point for running the application
if __name__ == "__main__":
    app = GeneWebApp()
    app.run(debug=True)