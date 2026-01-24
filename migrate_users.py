"""
Migration script to add user authentication support.
Run this once to:
1. Create the users table
2. Create an admin account (you'll be prompted for credentials or use env vars)
3. Add user_id columns to existing tables
4. Assign all existing data to the admin user

Works with both SQLite (local) and PostgreSQL (Render).
"""
from sqlalchemy import text, inspect
import os
import getpass


def migrate():
    from app import app, db
    from models import User

    with app.app_context():
        print("=" * 50)
        print("Garden Tracker - User Authentication Migration")
        print("=" * 50)

        # Detect database type
        db_url = str(db.engine.url)
        is_postgres = 'postgresql' in db_url or 'postgres' in db_url
        print(f"\nDatabase: {'PostgreSQL' if is_postgres else 'SQLite'}")

        # Create all tables (including users) if they don't exist
        db.create_all()
        print("Tables created/verified.")

        # Check if admin user already exists
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            print(f"\nAdmin user '{admin.username}' already exists.")
            print("Checking for user_id columns...")
        else:
            # Get admin credentials from environment or prompt
            print("\n" + "-" * 50)
            print("Create your admin account:")
            print("-" * 50)

            # Check for environment variables (for automated deployment)
            username = os.environ.get('ADMIN_USERNAME', '').strip()
            email = os.environ.get('ADMIN_EMAIL', '').strip()
            password = os.environ.get('ADMIN_PASSWORD', '')

            if not username:
                username = input("Username: ").strip()
                while not username:
                    print("Username cannot be empty.")
                    username = input("Username: ").strip()

            if not email:
                email = input("Email: ").strip()
                while not email or '@' not in email:
                    print("Please enter a valid email.")
                    email = input("Email: ").strip()

            if not password:
                password = getpass.getpass("Password: ")
                while len(password) < 4:
                    print("Password must be at least 4 characters.")
                    password = getpass.getpass("Password: ")

                password_confirm = getpass.getpass("Confirm password: ")
                while password != password_confirm:
                    print("Passwords don't match. Try again.")
                    password = getpass.getpass("Password: ")
                    password_confirm = getpass.getpass("Confirm password: ")

            # Create admin user
            admin = User(
                username=username,
                email=email,
                is_admin=True
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"\nAdmin user '{username}' created!")

        # Add user_id columns to existing tables if needed
        print("\nChecking user_id columns in existing tables...")

        inspector = inspect(db.engine)
        tables = ['seeds', 'grow_bags', 'seedlings', 'plants']

        for table in tables:
            try:
                # Check if table exists
                if table not in inspector.get_table_names():
                    print(f"  Table {table} doesn't exist yet, skipping.")
                    continue

                # Check if column exists
                columns = [col['name'] for col in inspector.get_columns(table)]

                if 'user_id' not in columns:
                    # Add the column
                    with db.engine.connect() as conn:
                        if is_postgres:
                            conn.execute(text(
                                f"ALTER TABLE {table} ADD COLUMN user_id INTEGER DEFAULT {admin.id}"
                            ))
                        else:
                            conn.execute(text(
                                f"ALTER TABLE {table} ADD COLUMN user_id INTEGER DEFAULT {admin.id}"
                            ))
                        conn.commit()
                    print(f"  Added user_id to {table}")

                # Update any NULL user_id values
                with db.engine.connect() as conn:
                    result = conn.execute(text(
                        f"UPDATE {table} SET user_id = {admin.id} WHERE user_id IS NULL"
                    ))
                    conn.commit()
                    if result.rowcount > 0:
                        print(f"  Assigned {result.rowcount} existing {table} to admin user")
                    else:
                        print(f"  {table} OK")

            except Exception as e:
                print(f"  Warning: Could not modify {table}: {e}")

        print("\n" + "=" * 50)
        print("Migration complete!")
        print("=" * 50)
        print(f"\nYou can now log in with:")
        print(f"  Username: {admin.username}")
        print(f"  Password: (the password you set)")
        print("\nRun 'python app.py' to start the application.")


if __name__ == '__main__':
    migrate()
