import sqlite3
import os
import json
from datetime import datetime
import shutil

def migrate_database():
    """Migrate the database to include the new column by creating a new database structure"""
    
    # Define database path
    db_path = 'smartlead.db'
    backup_path = 'smartlead_backup.db'
    
    # Backup existing database
    print(f"Creating backup of database to {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()
    
    # Get all existing campaigns
    print("Extracting existing campaign data...")
    cursor.execute("SELECT * FROM campaign")
    campaigns = [dict(row) for row in cursor.fetchall()]
    
    # Get all other relevant data you want to preserve
    cursor.execute("SELECT * FROM contact")
    contacts = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM email_template")
    templates = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM email_sequence")
    sequences = [dict(row) for row in cursor.fetchall()]
    
    # Get user data
    cursor.execute("SELECT * FROM user")
    users = [dict(row) for row in cursor.fetchall()]
    
    # Recreate the campaign table with the new column
    print("Recreating campaign table with new column...")
    cursor.execute("DROP TABLE IF EXISTS campaign")
    cursor.execute("""
    CREATE TABLE campaign (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        status VARCHAR(20) DEFAULT 'draft',
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        smartlead_id INTEGER UNIQUE,
        smartlead_stats_json TEXT,
        branch_data_json TEXT
    )
    """)
    
    # Reinsert the campaign data
    print(f"Reinserting {len(campaigns)} campaigns...")
    for campaign in campaigns:
        cursor.execute("""
        INSERT INTO campaign (id, name, description, status, created_at, updated_at, smartlead_id, smartlead_stats_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign['id'],
            campaign['name'],
            campaign['description'],
            campaign['status'],
            campaign['created_at'],
            campaign['updated_at'],
            campaign['smartlead_id'],
            campaign['smartlead_stats_json']
        ))
    
    # Commit changes and close
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")
    print(f"Your original database has been backed up to {backup_path}")

if __name__ == "__main__":
    migrate_database() 