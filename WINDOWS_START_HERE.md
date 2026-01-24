# WINDOWS USERS - START HERE! 🪟

## Quick Fix for Installation Error

You got an error because PostgreSQL isn't installed. **Good news: You don't need it!**

## Two Options:

### Option 1: SQLite (RECOMMENDED - Super Easy!)

Just run this file instead:
```
start-sqlite.bat
```

**That's it!** Double-click `start-sqlite.bat` and everything will work.

### Option 2: Manual Setup (if batch file doesn't work)

```cmd
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install ONLY the SQLite dependencies
pip install -r requirements-sqlite.txt

# 3. Create .env file with this content:
copy .env.example .env
# Edit .env and set: DATABASE_URL=sqlite:///garden_tracker.db

# 4. Add sample data
python init_db.py

# 5. Run it!
python app.py
```

Visit: http://localhost:5000

## What's the Difference?

- **requirements.txt** = PostgreSQL version (needs PostgreSQL installed)
- **requirements-sqlite.txt** = SQLite version (no extra software needed)

SQLite is perfect for personal use and much simpler on Windows!

## Still Having Issues?

Make sure Python is installed:
1. Download from https://www.python.org/downloads/
2. During installation, CHECK "Add Python to PATH"
3. Restart Command Prompt
4. Try again

## Next Steps

Once running:
1. Add your seed varieties
2. Set up grow bags  
3. Start tracking seedlings
4. Log harvests!

The sample data includes tomatoes, peppers, and herbs to get you started. 🌱🍅🌶️
