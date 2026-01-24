# Garden Tracker - Project Overview

## 🎉 Complete Garden Management Application

A full-featured Flask application for tracking your hydroponic/container garden with:
- Seed inventory management
- Seedling tracking from germination to transplant
- Grow bag/container capacity planning
- Individual plant lifecycle tracking
- Harvest logging and yield analysis
- Variety performance comparisons
- Automatic planting date calculations for Zone 7a/b

## 📁 Project Structure

```
garden-tracker/
├── app.py                    # Main Flask application with all routes
├── models.py                 # SQLAlchemy database models
├── config.py                 # Application configuration
├── init_db.py               # Database initialization with sample data
├── requirements.txt          # Python dependencies
├── start.sh                 # Automated setup and start script
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # Comprehensive documentation
├── QUICKSTART.md           # Quick setup guide
│
└── templates/              # HTML templates
    ├── base.html          # Base template with navigation
    ├── dashboard.html     # Main dashboard
    ├── analytics.html     # Analytics and reports
    ├── calendar.html      # Planting calendar
    │
    ├── seeds/            # Seed management templates
    │   ├── list.html
    │   ├── add.html
    │   ├── detail.html
    │   └── edit.html
    │
    ├── seedlings/        # Seedling tracking templates
    │   ├── list.html
    │   ├── add.html
    │   └── detail.html
    │
    ├── growbags/         # Container management templates
    │   ├── list.html
    │   ├── add.html
    │   └── detail.html
    │
    ├── plants/           # Plant tracking templates
    │   ├── list.html
    │   ├── add.html
    │   └── detail.html
    │
    └── harvests/         # Harvest logging templates
        ├── list.html
        └── add.html
```

## 🗄️ Database Schema

### Seeds
- Tracks seed inventory with variety details
- Germination rates, expiration dates
- Days to maturity, weeks to transplant
- Supplier information

### Seedlings
- Monitors from germination to transplant
- Tracks quantity started vs viable
- Auto-calculates expected transplant dates
- Status tracking (germinating, growing, ready, transplanted, failed)

### GrowBags (Containers)
- Container information (size, location)
- Capacity tracking (max plants, current count)
- Available space calculations

### Plants
- Individual plant lifecycle tracking
- Links to seed variety and seedling
- Auto-calculates expected harvest dates
- Status tracking (growing, flowering, producing, dormant, dead)
- Health ratings

### Harvests
- Yield tracking with amounts and units
- Quality ratings (1-10 scale)
- Links to specific plants

### ProgressLogs
- Track plant growth over time
- Height measurements, growth stages
- Observations, issues, actions taken

### PlantingCalendar
- Pre-defined planting schedules
- Zone-specific timing
- Succession planting recommendations

## 🚀 Key Features

### Smart Date Calculations
- **Seed Start Dates**: Automatically calculated based on transplant date and weeks to maturity
- **Transplant Dates**: Calculated from last frost date for your zone
- **Expected Harvest**: Calculated from transplant date and days to maturity
- **Days Since**: Tracks days since germination or transplant

### Dashboard Insights
- Active plants and seedlings count
- Seedlings ready to transplant (with alerts)
- Upcoming harvests (next 2 weeks)
- Recent harvests (last 7 days)
- Low seed inventory warnings
- Available grow bag space

### Analytics
- Variety performance comparisons
- Total and average yields per variety
- Quality ratings by variety
- Monthly harvest trends
- Best performing plants

### Container Management
- Track capacity across all grow bags
- See which containers have space
- Organize by location
- Plan container layouts

## 🎨 Design Philosophy

**Desktop-Focused Interface**
- Clean, professional layout
- No excessive JavaScript
- Fast page loads
- Keyboard-friendly forms

**Data-Driven**
- Everything is tracked for analysis
- Compare varieties objectively
- Make informed planting decisions

**Zone-Specific**
- Configured for Zone 7a/b
- Easily customizable for other zones
- Frost date calculations

**Modular & Extensible**
- Clean separation of concerns
- Easy to add new features
- Well-documented code

## 💾 Technology Stack

- **Backend**: Python 3.8+ with Flask 3.0
- **Database**: PostgreSQL (or SQLite)
- **ORM**: SQLAlchemy
- **Frontend**: HTML5, CSS3 (minimal JavaScript)
- **Styling**: Custom CSS (no framework bloat)

## 📊 Sample Data

The `init_db.py` script includes:
- 7 seed varieties (San Marzano tomato, Cherokee Purple tomato, Jalapeño, Carolina Reaper, Bell Pepper, Basil, Cucumber)
- 7 grow bags (various sizes and locations)
- Planting calendar entries for common vegetables
- Pre-configured for Zone 7a/b timing

## 🔧 Customization Options

### Change Your Growing Zone
Edit `.env`:
```
LAST_FROST_DATE=04-15  # April 15 for Zone 7a/b
FIRST_FROST_DATE=10-15  # October 15 for Zone 7a/b
```

### Add Plant Types
Edit `templates/seeds/add.html` to add more plant type options

### Modify Units
Edit harvest form to add custom units (grams, kg, etc.)

### Extend Database
Add new models in `models.py` and create corresponding routes in `app.py`

## 🎯 Future Enhancement Ideas

- Photo upload for plants and harvests
- Weather API integration
- Pest/disease tracking with treatment logs
- Fertilizer schedules
- Watering reminders
- Companion planting suggestions
- Export to CSV/PDF
- Multi-user support with shared gardens
- Mobile responsive design
- RESTful API

## 📝 Setup Instructions

### Method 1: Automated (Recommended)
```bash
chmod +x start.sh
./start.sh
```

### Method 2: Manual
```bash
# 1. Create database
createdb garden_tracker

# 2. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 3. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Initialize with sample data (optional)
python init_db.py

# 5. Run application
python app.py
```

Visit http://localhost:5000

## 🎓 Learning Opportunities

This project demonstrates:
- Flask application structure
- SQLAlchemy ORM relationships
- Database design for domain-specific applications
- Template inheritance with Jinja2
- Form handling and validation
- Date/time calculations in Python
- CRUD operations
- Data aggregation and analytics
- Clean, maintainable code organization

## 🐛 Troubleshooting

**Database Connection Issues**
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL in `.env`
- Ensure database exists

**Import Errors**
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Port Already in Use**
- Change port in `app.py`: `app.run(debug=True, port=5001)`

## 📄 License

Free to use and modify for personal gardening projects.

## 🌱 Happy Growing!

This application was built to help you:
- Track what works and what doesn't
- Optimize your planting schedule
- Maximize yields from limited space
- Make data-driven gardening decisions
- Learn from each growing season

Start tracking your garden today! 🍅🌶️🥒
