# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Garden Tracker is a Flask web application for Zone 7a/b container gardening. It tracks seeds, seedlings, plants, harvests, and provides planting schedules based on frost dates.

## Commands

### Run the Application
```bash
# Activate virtual environment first
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix

# Run development server
python app.py
```
The app runs at http://localhost:5000.

### Database Setup
```bash
# Initialize with sample data (optional)
python init_db.py
```
Tables are auto-created on first run via `db.create_all()` in app.py.

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Core Files
- **app.py** - Flask routes and application logic (single-file app pattern)
- **models.py** - SQLAlchemy models with Flask-SQLAlchemy
- **config.py** - Configuration including frost date calculations

### Database Models (models.py)
The data model follows the plant lifecycle:

```
Seed → Seedling → Plant → Harvest
                    ↓
              ProgressLog
                    ↓
               GrowBag (container)
```

- **Seed**: Inventory tracking with germination/maturity calculations
- **Seedling**: Tracks germination through transplant readiness
- **Plant**: Active plants linked to seeds, seedlings, and containers
- **Harvest**: Yield records with quality ratings
- **ProgressLog**: Growth observations and issues
- **GrowBag**: Container capacity tracking
- **PlantingCalendar**: Zone-based planting schedules

### Key Patterns
- Models have computed properties (`total_yield`, `days_since_transplant`, `is_full`)
- Date calculations use `timedelta` for frost-date-relative scheduling
- Cascading relationships handle child record deletion (Plant → Harvest, ProgressLog)

### Templates Structure
Templates use Jinja2 with a `base.html` layout. Organized by entity:
- `templates/seeds/` - Seed CRUD views
- `templates/seedlings/` - Seedling management
- `templates/plants/` - Plant tracking
- `templates/growbags/` - Container management
- `templates/harvests/` - Harvest recording
- `templates/dashboard.html` - Main overview
- `templates/analytics.html` - Variety comparisons
- `templates/calendar.html` - Planting schedule

### Configuration
Environment variables (`.env`):
- `DATABASE_URL` - PostgreSQL connection (defaults to SQLite if not set)
- `LAST_FROST_DATE` / `FIRST_FROST_DATE` - Zone-specific dates in MM-DD format

## Database

Supports PostgreSQL (production) or SQLite (development fallback). The connection string in `DATABASE_URL` determines which is used.
