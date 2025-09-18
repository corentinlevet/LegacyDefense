#!/usr/bin/env python3
"""
Simple startup script for GeneWeb Python application.
"""
import uvicorn
from core.webapp import GeneWebApp

def main():
    """Start the GeneWeb application."""
    # Create app instance
    app_instance = GeneWebApp("sqlite:///geneweb.db")
    
    # Start server
    print("Starting GeneWeb on http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        app_instance.app, 
        host="0.0.0.0", 
        port=8000,
        reload=False
    )

if __name__ == "__main__":
    main()