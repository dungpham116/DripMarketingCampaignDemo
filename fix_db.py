import sqlite3
import os

def add_column_direct():
    """Add branch_data_json column directly to the database"""
    # Get database path from environment or use default
    db_path = os.environ.get('DATABASE_URL', 'sqlite:///smartlead.db')
    
    # Strip sqlite:/// if present
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]
    
    print(f"Connecting to database at {db_path}")
    
    # Connect directly to the SQLite database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add the column
        cursor.execute("ALTER TABLE campaign ADD COLUMN branch_data_json TEXT")
        conn.commit()
        print("Column 'branch_data_json' added successfully")
        
        # Verify the column exists
        cursor.execute("PRAGMA table_info(campaign)")
        columns = cursor.fetchall()
        print("Campaign table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    add_column_direct() 