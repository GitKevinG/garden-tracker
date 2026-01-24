# Garden Tracker - Quick Setup Guide

## Prerequisites
- Python 3.8+
- PostgreSQL 12+

## Quick Start (3 Steps!)

### 1. Set up database
```bash
# Create the database
createdb garden_tracker

# Or using psql:
psql -U postgres
CREATE DATABASE garden_tracker;
\q
```

### 2. Configure and install
```bash
# Copy environment file
cp .env.example .env

# Edit .env with your database credentials:
# DATABASE_URL=postgresql://YOUR_USERNAME:YOUR_PASSWORD@localhost:5432/garden_tracker

# Create virtual environment and install
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initialize and run
```bash
# Add sample data (optional but recommended for first time)
python init_db.py

# Start the application
python app.py
```

Visit **http://localhost:5000** in your browser!

## Alternative: Use the automatic setup script

```bash
chmod +x start.sh
./start.sh
```

This script will:
- Check for Python and PostgreSQL
- Create virtual environment
- Install dependencies
- Create database (if needed)
- Optionally add sample data
- Start the application

## First Time Usage

Once the app is running:

1. **Add your seeds**: Go to Seeds → Add New Seed
   - Include variety names, days to maturity, weeks to transplant
   - This enables automatic date calculations!

2. **Set up grow bags**: Go to Grow Bags → Add Grow Bag
   - Specify size and location
   - Set max plants per container

3. **Start seedlings**: Go to Seedlings → Start New Seedlings
   - Select seed variety
   - Enter germination date
   - System calculates transplant date automatically!

4. **Track everything**: 
   - Transplant seedlings to grow bags
   - Log plant progress regularly
   - Record harvests with quality ratings

## Sample Data Included

If you ran `init_db.py`, you'll have:
- 7 seed varieties (tomatoes, peppers, herbs, cucumber)
- 7 grow bags in various sizes
- Planting calendar entries for Zone 7a/b

## Customization

### Adjust for your zone
Edit `.env`:
```
LAST_FROST_DATE=04-15  # Your last frost date (MM-DD)
FIRST_FROST_DATE=10-15  # Your first frost date (MM-DD)
```

### Change database
Using SQLite instead of PostgreSQL? Update `.env`:
```
DATABASE_URL=sqlite:///garden_tracker.db
```

## Troubleshooting

**Can't connect to database?**
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in .env
- Make sure database exists: `psql -l | grep garden_tracker`

**Tables not created?**
- They're created automatically on first run
- Check for error messages in terminal

**Port 5000 already in use?**
- Change port in app.py: `app.run(debug=True, port=5001)`

## Features Overview

### Core Features
- ✅ Seed inventory with germination rates
- ✅ Seedling tracking from germination to transplant
- ✅ Grow bag/container management
- ✅ Individual plant tracking
- ✅ Harvest logging with quality ratings
- ✅ Progress logs for plant health

### Smart Calculations
- ✅ Auto-calculate seed start dates
- ✅ Auto-calculate transplant dates  
- ✅ Auto-calculate expected harvest dates
- ✅ Track days since germination/transplant

### Analytics
- ✅ Compare variety performance
- ✅ Track yields over time
- ✅ Quality ratings
- ✅ Best performing varieties

### Planning
- ✅ Planting calendar for your zone
- ✅ Container space management
- ✅ Ready-to-transplant alerts
- ✅ Upcoming harvest predictions

## Next Steps

Check out the full README.md for:
- Detailed usage guide
- Database schema details
- Extension ideas
- Best practices

Happy growing! 🌱🍅🌶️
