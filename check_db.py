from app import create_app, db
import os
import sqlite3

def check_db():
    """Check database connection and structure"""
    app = create_app()
    with app.app_context():
        # Print the actual database URI being used
        print(f"SQLAlchemy Database URI: {db.engine.url}")
        
        # Check if database file exists
        db_path = str(db.engine.url).replace('sqlite:///', '')
        print(f"Database file path: {db_path}")
        print(f"File exists: {os.path.exists(db_path)}")
        
        # Directly inspect database structure
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            print("\nTables in database:")
            for table in cursor.fetchall():
                print(f"  - {table[0]}")
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"      {col[1]} ({col[2]})")
            conn.close()
        except Exception as e:
            print(f"Error inspecting database: {str(e)}")

if __name__ == "__main__":
    check_db() 