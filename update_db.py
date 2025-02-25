from app import create_app, db
from sqlalchemy import text

def add_branch_data_column():
    """Add branch_data_json column to Campaign table if it doesn't exist"""
    app = create_app()
    with app.app_context():
        try:
            # Try to select from the column to see if it exists
            db.session.execute(text("SELECT branch_data_json FROM campaign LIMIT 1"))
            print("Column 'branch_data_json' already exists in Campaign table")
        except Exception as e:
            # If it fails, the column doesn't exist, so add it
            print("Adding 'branch_data_json' column to Campaign table")
            db.session.execute(text("ALTER TABLE campaign ADD COLUMN branch_data_json TEXT"))
            db.session.commit()
            print("Column added successfully")

if __name__ == "__main__":
    add_branch_data_column() 