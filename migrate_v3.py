"""
Migration script to make germination_date nullable in seedlings table.
SQLite doesn't support ALTER COLUMN, so we need to recreate the table.
"""
from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        conn = db.engine.connect()

        print("Making germination_date nullable in seedlings table...")

        # Create new table with correct schema
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS seedlings_new (
                id INTEGER PRIMARY KEY,
                seed_id INTEGER NOT NULL,
                sown_date DATE,
                germination_date DATE,
                quantity_started INTEGER DEFAULT 1,
                quantity_viable INTEGER,
                expected_transplant_date DATE,
                actual_transplant_date DATE,
                potted_up_date DATE,
                pot_size VARCHAR(20),
                quantity_potted_up INTEGER,
                location VARCHAR(100),
                status VARCHAR(20) DEFAULT 'germinating',
                notes TEXT,
                created_at DATETIME,
                FOREIGN KEY (seed_id) REFERENCES seeds(id)
            )
        """))

        # Copy data from old table (use germination_date as sown_date for existing records if sown_date is null)
        conn.execute(text("""
            INSERT INTO seedlings_new
            SELECT
                id, seed_id,
                COALESCE(sown_date, germination_date) as sown_date,
                germination_date,
                quantity_started, quantity_viable,
                expected_transplant_date, actual_transplant_date,
                potted_up_date, pot_size, quantity_potted_up,
                location, status, notes, created_at
            FROM seedlings
        """))

        # Drop old table
        conn.execute(text("DROP TABLE seedlings"))

        # Rename new table
        conn.execute(text("ALTER TABLE seedlings_new RENAME TO seedlings"))

        conn.commit()
        conn.close()
        print("Migration complete! germination_date is now nullable.")

if __name__ == '__main__':
    migrate()
