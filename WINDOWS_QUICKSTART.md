# Garden Tracker - Windows Quick Start

## For Windows Users

### Option 1: Automated Setup (Recommended)

Just double-click `start.bat` or run from command prompt:

```cmd
start.bat
```

This will:
- Create virtual environment
- Install dependencies
- Prompt you to configure database
- Optionally add sample data
- Start the application

### Option 2: Manual Setup

#### Step 1: Choose Your Database

**Option A: SQLite (Simpler - No Installation Needed)**
1. Copy `.env.example` to `.env`
2. Edit `.env` and set:
   ```
   DATABASE_URL=sqlite:///garden_tracker.db
   ```

**Option B: PostgreSQL (More Robust)**
1. Install PostgreSQL from https://www.postgresql.org/download/windows/
2. Open pgAdmin or Command Prompt with psql
3. Create database:
   ```sql
   CREATE DATABASE garden_tracker;
   ```
4. Copy `.env.example` to `.env`
5. Edit `.env` and set:
   ```
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/garden_tracker
   ```

#### Step 2: Set Up Python Environment

```cmd
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Initialize and Run

```cmd
# Add sample data (optional but recommended first time)
python init_db.py

# Start the application
python app.py
```

Visit **http://localhost:5000** in your browser!

## Troubleshooting Windows Issues

### "python not found"
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation
- Restart Command Prompt after installation

### "pip not found" 
```cmd
python -m pip install --upgrade pip
```

### Virtual environment activation fails
If `venv\Scripts\activate.bat` doesn't work, try:
```cmd
venv\Scripts\activate.ps1
```

Or run Python directly:
```cmd
venv\Scripts\python.exe app.py
```

### Port 5000 already in use
Edit `app.py` and change the last line to:
```python
app.run(debug=True, port=5001)
```

### PostgreSQL connection issues
Try SQLite instead - it requires zero setup:
- Edit `.env`: `DATABASE_URL=sqlite:///garden_tracker.db`
- Delete any existing database files
- Run `python app.py`

## What's Next?

Once running:

1. **Add Your Seeds** 
   - Go to Seeds → Add New Seed
   - Enter variety details and growing specs

2. **Set Up Grow Bags**
   - Go to Grow Bags → Add Grow Bag
   - Enter size, location, capacity

3. **Start Seedlings**
   - Go to Seedlings → Start New Seedlings
   - System auto-calculates transplant dates!

4. **Track Everything**
   - Transplant to grow bags
   - Log progress regularly
   - Record harvests

## Sample Data Included

If you ran `init_db.py`, you have:
- 7 seed varieties (tomatoes, peppers, herbs, cucumber)
- 7 grow bags ready to use
- Planting calendar for Zone 7a/b

Perfect for testing the system before adding your own data!

## File Locations on Windows

- **Application**: `C:\Users\YourName\Projects\garden-tracker\`
- **Database (SQLite)**: `C:\Users\YourName\Projects\garden-tracker\garden_tracker.db`
- **Virtual Environment**: `C:\Users\YourName\Projects\garden-tracker\venv\`

## Deactivating Virtual Environment

When done:
```cmd
deactivate
```

## Need Help?

Check the full documentation:
- `README.md` - Complete guide
- `PROJECT_OVERVIEW.md` - Technical details
- `QUICKSTART.md` - Linux/Mac guide

Happy Growing! 🌱🍅🌶️
