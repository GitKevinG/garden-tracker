"""
Migration script for garden tracker v2:
- Add size_category to seeds
- Add potting up fields to seedlings
"""
from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        conn = db.engine.connect()

        # Add size_category to seeds
        try:
            conn.execute(text("ALTER TABLE seeds ADD COLUMN size_category VARCHAR(20) DEFAULT 'medium'"))
            print("Added size_category to seeds table")
        except Exception as e:
            print(f"size_category may already exist: {e}")

        # Add potting up fields to seedlings
        try:
            conn.execute(text("ALTER TABLE seedlings ADD COLUMN sown_date DATE"))
            print("Added sown_date to seedlings table")
        except Exception as e:
            print(f"sown_date may already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE seedlings ADD COLUMN potted_up_date DATE"))
            print("Added potted_up_date to seedlings table")
        except Exception as e:
            print(f"potted_up_date may already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE seedlings ADD COLUMN pot_size VARCHAR(20)"))
            print("Added pot_size to seedlings table")
        except Exception as e:
            print(f"pot_size may already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE seedlings ADD COLUMN quantity_potted_up INTEGER"))
            print("Added quantity_potted_up to seedlings table")
        except Exception as e:
            print(f"quantity_potted_up may already exist: {e}")

        conn.commit()
        conn.close()
        print("\nMigration complete!")

if __name__ == '__main__':
    migrate()
