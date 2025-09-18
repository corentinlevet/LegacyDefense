#!/usr/bin/env python3
"""
Quick fix for enum issues in the database.
This script will temporarily fix the 'sure' vs 'SURE' enum problem.
"""

import sqlite3
import os
from pathlib import Path

def fix_enum_values():
    """Fix the DatePrecision enum values in the database."""
    
    # Find the database file
    db_path = Path("geneweb.db")
    if not db_path.exists():
        print("Database file not found. Looking for alternatives...")
        # Try other common locations
        for possible_path in ["data/geneweb.db", "../geneweb.db", "core/geneweb.db"]:
            if Path(possible_path).exists():
                db_path = Path(possible_path)
                break
        else:
            print("No database file found!")
            return False
    
    print(f"Found database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check current enum values
        cursor.execute("SELECT DISTINCT precision FROM dates")
        current_precisions = cursor.fetchall()
        print(f"Current precision values: {current_precisions}")
        
        # Update lowercase to uppercase
        cursor.execute("UPDATE dates SET precision = 'SURE' WHERE precision = 'sure'")
        cursor.execute("UPDATE dates SET precision = 'ABOUT' WHERE precision = 'about'")
        cursor.execute("UPDATE dates SET precision = 'MAYBE' WHERE precision = 'maybe'")
        cursor.execute("UPDATE dates SET precision = 'BEFORE' WHERE precision = 'before'")
        cursor.execute("UPDATE dates SET precision = 'AFTER' WHERE precision = 'after'")
        cursor.execute("UPDATE dates SET precision = 'OR_YEAR' WHERE precision = 'or_year'")
        cursor.execute("UPDATE dates SET precision = 'YEAR_INT' WHERE precision = 'year_int'")
        
        # Commit changes
        conn.commit()
        
        # Verify changes
        cursor.execute("SELECT DISTINCT precision FROM dates")
        new_precisions = cursor.fetchall()
        print(f"Updated precision values: {new_precisions}")
        
        # Close connection
        conn.close()
        
        print("✅ Database enum values fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False

if __name__ == "__main__":
    fix_enum_values()