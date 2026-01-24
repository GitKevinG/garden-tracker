# Garden Tracker

A comprehensive garden management application for Zone 7a/b container gardening. Track your seeds, seedlings, plants, harvests, and optimize your growing schedule.

## Features

### 🌱 Core Tracking
- **Seed Inventory**: Track varieties, quantities, germination rates, and expiration dates
- **Seedling Management**: Monitor seedlings from germination through transplant
- **Plant Tracking**: Follow individual plants through their lifecycle
- **Harvest Logging**: Record yields, quality ratings, and compare varieties
- **Progress Logs**: Document plant growth, health, and issues over time

### 📅 Planning & Scheduling
- **Planting Calendar**: Automatic calculation of seed start and transplant dates based on Zone 7a/b frost dates
- **Smart Date Calculations**: System calculates expected harvest dates based on days to maturity
- **Transplant Timing**: Track when seedlings are ready to move outdoors

### 🪴 Container Management
- **Grow Bag Tracking**: Monitor container capacity and current plantings
- **Space Planning**: See available spaces across all containers
- **Location Organization**: Group containers by location (balcony, deck, etc.)

### 📊 Analytics
- **Variety Comparison**: Compare performance across different varieties
- **Yield Analysis**: Track total and average yields per plant
- **Monthly Trends**: View harvest patterns over time
- **Quality Ratings**: Rate and compare harvest quality

## Technology Stack

- **Backend**: Python 3.x with Flask
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Frontend**: HTML5, CSS3 (no JavaScript framework - desktop-focused)

## Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher

### Setup

1. **Clone or download this repository**

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL database**
```bash
# Create database
createdb garden_tracker

# Or using psql
psql -U postgres
CREATE DATABASE garden_tracker;
\q
```

5. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

Example `.env` file:
```
DATABASE_URL=postgresql://username:password@localhost:5432/garden_tracker
SECRET_KEY=your-secret-key-here-change-this
FLASK_ENV=development
LAST_FROST_DATE=04-15
FIRST_FROST_DATE=10-15
```

6. **Initialize the database**
```bash
python app.py
# The database tables will be created automatically on first run
```

7. **Run the application**
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## Database Models

### Seed
Tracks seed inventory with variety information, quantity, and growing specifications.

**Key Fields**:
- variety_name, plant_type, quantity
- days_to_maturity, weeks_to_transplant
- germination_rate, expiration_date
- supplier, purchase_date

### Seedling
Monitors seedlings from germination to transplant readiness.

**Key Fields**:
- seed_id (foreign key)
- germination_date, expected_transplant_date
- quantity_started, quantity_viable
- status (germinating, growing, ready, transplanted, failed)
- location

### GrowBag
Manages container information and capacity tracking.

**Key Fields**:
- name, size_gallons, location
- max_plants, current_plants
- Calculated: is_full, available_space

### Plant
Tracks individual plants from transplant through harvest.

**Key Fields**:
- seed_id, seedling_id, grow_bag_id (foreign keys)
- transplant_date, expected_harvest_date
- first_harvest_date, last_harvest_date
- status (growing, flowering, producing, dormant, dead)
- health_rating

### Harvest
Records harvest yields with quality ratings.

**Key Fields**:
- plant_id (foreign key)
- harvest_date, amount, unit
- quality_rating (1-10 scale)

### ProgressLog
Documents plant progress over time.

**Key Fields**:
- plant_id (foreign key)
- log_date, height_inches, growth_stage
- observations, issues, actions_taken

### PlantingCalendar
Pre-defined planting schedules for different varieties.

**Key Fields**:
- plant_type, variety_name
- weeks_before_last_frost, weeks_after_last_frost
- succession_planting_weeks

## Usage Guide

### Getting Started

1. **Add Seeds to Inventory**
   - Go to Seeds → Add New Seed
   - Enter variety details, quantity, and growing specs
   - Include days to maturity and weeks to transplant for automatic date calculations

2. **Start Seedlings**
   - Go to Seedlings → Start New Seedlings
   - Select seed variety and germination date
   - System automatically calculates expected transplant date

3. **Add Grow Bags**
   - Go to Grow Bags → Add Grow Bag
   - Specify size, location, and max plant capacity
   - Track available space across all containers

4. **Transplant Plants**
   - When seedlings are ready, go to Plants → Add Plant
   - Link to seedling (optional) and assign to grow bag
   - System calculates expected harvest date

5. **Log Progress**
   - Click on any plant to view details
   - Add progress logs to track growth, health, and issues
   - Document height, growth stage, and any problems

6. **Record Harvests**
   - Go to Harvests → Add Harvest
   - Select plant, enter amount and quality rating
   - Track yields over time for each variety

### Dashboard Features

The dashboard provides an at-a-glance view of:
- Active plants and seedlings count
- Available grow bag spaces
- Seedlings ready to transplant
- Upcoming harvests (next 2 weeks)
- Recent harvests (last 7 days)
- Low seed inventory alerts

### Analytics

View comprehensive analytics including:
- **Variety Performance**: Compare total yields, plant counts, and quality ratings
- **Monthly Trends**: See harvest patterns throughout the growing season
- **Best Performers**: Identify your most productive varieties

### Planting Calendar

Automatic planting schedule generation based on:
- Zone 7a/b frost dates (configurable in .env)
- Variety-specific timing requirements
- Succession planting recommendations

## Customization

### Adjusting Frost Dates

Edit `.env` to match your specific location:
```
LAST_FROST_DATE=04-15  # April 15
FIRST_FROST_DATE=10-15  # October 15
```

### Adding Plant Types

Edit the plant_type dropdown in `templates/seeds/add.html` to add your preferred plant types.

### Database Backup

Regular backups recommended:
```bash
pg_dump garden_tracker > backup_$(date +%Y%m%d).sql
```

## Development

### Project Structure
```
garden-tracker/
├── app.py              # Main Flask application
├── models.py           # Database models
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── seeds/
│   ├── seedlings/
│   ├── growbags/
│   ├── plants/
│   └── harvests/
└── .env               # Environment variables (create from .env.example)
```

### Adding Features

The modular structure makes it easy to extend:
1. Add new models in `models.py`
2. Create routes in `app.py`
3. Add templates in `templates/`
4. Use the existing CSS classes for consistent styling

## Tips for Success

1. **Start with seed data**: Add all your seed varieties first with accurate days to maturity
2. **Track everything**: More data = better insights into what works
3. **Use progress logs**: Regular observations help catch problems early
4. **Compare varieties**: Use analytics to identify your best performers
5. **Plan ahead**: Use the planting calendar to time your seed starts
6. **Update seedling status**: Keep seedling status current for accurate transplant planning

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL in .env
- Ensure database exists: `psql -l | grep garden_tracker`

### Missing Tables
- Tables are created automatically on first run
- Force recreation: Drop database and restart app

### Date Calculation Issues
- Verify frost dates in .env are in MM-DD format
- Ensure seeds have days_to_maturity and weeks_to_transplant set

## Future Enhancements

Potential features to add:
- Photo upload for plants and harvests
- Weather integration
- Pest and disease tracking with treatments
- Fertilizer and watering schedules
- Companion planting suggestions
- Seed trading/sharing with friends
- Mobile responsive design
- Export data to CSV

## License

Free to use and modify for personal gardening projects.

## Support

For questions or issues, refer to the inline comments in the code or create detailed bug reports with:
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable

Happy Growing! 🌱🍅🌶️
