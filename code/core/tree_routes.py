"""
Additional routes for tree visualization and advanced features.

This module adds routes to webapp.py for:
- Interactive D3.js family tree
- Tree data API endpoints
- Advanced search with the new search engine
"""

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import os

def add_tree_routes(app_instance):
    """Add tree visualization routes to the GeneWeb app."""
    
    @app_instance.app.get("/tree/interactive", response_class=HTMLResponse)
    async def tree_interactive(request: Request):
        """Interactive D3.js family tree visualization."""
        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "templates"
        )
        tree_html_path = os.path.join(templates_dir, "tree_interactive.html")
        
        if os.path.exists(tree_html_path):
            with open(tree_html_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            raise HTTPException(
                status_code=404, 
                detail="Tree template not found"
            )
    
    @app_instance.app.get("/api/tree/{tree_type}/{root_id}")
    async def get_tree_data(
        tree_type: str,
        root_id: int,
        max_gen: int = 4,
        db: Session = Depends(app_instance.get_db)
    ):
        """
        API endpoint to get tree data for D3.js visualization.
        
        Args:
            tree_type: 'ancestors', 'descendants', 'hourglass', or 'full'
            root_id: ID of the root person
            max_gen: Maximum generations to include
        """
        from core.database import PersonORM, FamilyORM
        
        root_person = db.query(PersonORM).filter(
            PersonORM.id == root_id
        ).first()
        
        if not root_person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        def person_to_dict(person):
            """Convert PersonORM to dict for JSON response."""
            return {
                "id": person.id,
                "name": f"{person.first_name} {person.surname}",
                "first_name": person.first_name,
                "surname": person.surname,
                "sex": person.sex,
                "birth": None,  # TODO: Get from events
                "death": None,
                "occupation": person.occupation,
                "children": []
            }
        
        def build_ancestor_tree(person, depth=0):
            """Build ancestor tree recursively."""
            if depth >= max_gen or not person:
                return None
            
            node = person_to_dict(person)
            
            if person.parent_family:
                children = []
                if person.parent_family.father:
                    father_node = build_ancestor_tree(
                        person.parent_family.father, depth + 1
                    )
                    if father_node:
                        children.append(father_node)
                
                if person.parent_family.mother:
                    mother_node = build_ancestor_tree(
                        person.parent_family.mother, depth + 1
                    )
                    if mother_node:
                        children.append(mother_node)
                
                node["children"] = children
            
            return node
        
        def build_descendant_tree(person, depth=0):
            """Build descendant tree recursively."""
            if depth >= max_gen or not person:
                return None
            
            node = person_to_dict(person)
            
            # Get all families where this person is a parent
            families = db.query(FamilyORM).filter(
                (FamilyORM.father_id == person.id) | 
                (FamilyORM.mother_id == person.id)
            ).all()
            
            children = []
            for family in families:
                family_children = db.query(PersonORM).filter(
                    PersonORM.parent_family_id == family.id
                ).all()
                
                for child in family_children:
                    child_node = build_descendant_tree(child, depth + 1)
                    if child_node:
                        children.append(child_node)
            
            node["children"] = children
            return node
        
        # Build the appropriate tree based on type
        if tree_type == "ancestors":
            tree_data = build_ancestor_tree(root_person)
        elif tree_type == "descendants":
            tree_data = build_descendant_tree(root_person)
        elif tree_type == "hourglass":
            # Combine both ancestor and descendant trees
            ancestor_tree = build_ancestor_tree(root_person)
            descendant_tree = build_descendant_tree(root_person)
            tree_data = ancestor_tree
            if tree_data and descendant_tree:
                tree_data["children"].extend(
                    descendant_tree.get("children", [])
                )
        else:  # full
            tree_data = build_descendant_tree(root_person)
        
        return tree_data if tree_data else person_to_dict(root_person)
    
    @app_instance.app.get("/search/advanced", response_class=HTMLResponse)
    async def advanced_search_page(request: Request):
        """Serve the advanced search page."""
        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "templates"
        )
        search_html_path = os.path.join(templates_dir, "advanced_search.html")
        
        if os.path.exists(search_html_path):
            with open(search_html_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            raise HTTPException(
                status_code=404,
                detail="Advanced search template not found"
            )
    
    print("✅ Routes d'arbre interactif ajoutées:")
    print("   - GET /tree/interactive - Visualisation D3.js")
    print("   - GET /api/tree/{type}/{root_id} - API de données d'arbre")
    print("   - GET /search/advanced - Recherche avancée")
