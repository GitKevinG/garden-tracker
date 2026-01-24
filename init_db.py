"""
Initialize the database with sample data for testing
"""
from app import app, db
from models import Seed, GrowBag, PlantingCalendar
from datetime import datetime

def init_sample_data():
    """Add sample seeds, grow bags, and planting calendar"""
    with app.app_context():
        # Check if data already exists
        if Seed.query.first() is not None:
            print("Database already has data. Skipping initialization.")
            return
        
        print("Adding sample seeds...")
        
        # Sample Tomato Seeds
        seeds = [
            Seed(
                variety_name="San Marzano",
                plant_type="tomato",
                quantity=20,
                days_to_maturity=78,
                weeks_to_transplant=6,
                germination_rate=85.0,
                supplier="Baker Creek",
                notes="Great for sauce, determinate variety"
            ),
            Seed(
                variety_name="Cherokee Purple",
                plant_type="tomato",
                quantity=15,
                days_to_maturity=80,
                weeks_to_transplant=6,
                germination_rate=90.0,
                supplier="Seeds of Change",
                notes="Heirloom, indeterminate, excellent flavor"
            ),
            # Peppers
            Seed(
                variety_name="Jalapeño",
                plant_type="pepper",
                quantity=25,
                days_to_maturity=70,
                weeks_to_transplant=8,
                germination_rate=75.0,
                supplier="Johnny's Seeds",
                notes="Medium heat, versatile"
            ),
            Seed(
                variety_name="Carolina Reaper",
                plant_type="pepper",
                quantity=10,
                days_to_maturity=90,
                weeks_to_transplant=8,
                germination_rate=60.0,
                supplier="PuckerButt Pepper Company",
                notes="Extremely hot, long growing season"
            ),
            Seed(
                variety_name="Bell Pepper - California Wonder",
                plant_type="pepper",
                quantity=18,
                days_to_maturity=75,
                weeks_to_transplant=8,
                germination_rate=80.0,
                supplier="Burpee",
                notes="Sweet, thick walls, great for stuffing"
            ),
            # Herbs
            Seed(
                variety_name="Basil - Genovese",
                plant_type="herb",
                quantity=50,
                days_to_maturity=60,
                weeks_to_transplant=4,
                germination_rate=95.0,
                supplier="Botanical Interests",
                notes="Classic Italian basil"
            ),
            # Other vegetables
            Seed(
                variety_name="Cucumber - Straight Eight",
                plant_type="cucumber",
                quantity=12,
                days_to_maturity=58,
                weeks_to_transplant=3,
                germination_rate=85.0,
                supplier="Burpee",
                notes="Good for slicing, compact vines"
            ),
        ]
        
        for seed in seeds:
            db.session.add(seed)
        
        print(f"Added {len(seeds)} seed varieties")
        
        # Sample Grow Bags
        print("Adding sample grow bags...")
        
        growbags = [
            GrowBag(name="Balcony-1", size_gallons=5, location="Balcony", max_plants=1),
            GrowBag(name="Balcony-2", size_gallons=5, location="Balcony", max_plants=1),
            GrowBag(name="Balcony-3", size_gallons=5, location="Balcony", max_plants=1),
            GrowBag(name="Deck-Large-1", size_gallons=10, location="Deck", max_plants=2),
            GrowBag(name="Deck-Large-2", size_gallons=10, location="Deck", max_plants=2),
            GrowBag(name="Patio-Small-1", size_gallons=3, location="Patio", max_plants=1),
            GrowBag(name="Patio-Small-2", size_gallons=3, location="Patio", max_plants=1),
        ]
        
        for bag in growbags:
            db.session.add(bag)
        
        print(f"Added {len(growbags)} grow bags")
        
        # Sample Planting Calendar for Zone 7a/b
        print("Adding planting calendar entries...")
        
        calendar_entries = [
            PlantingCalendar(
                plant_type="tomato",
                weeks_before_last_frost=6,
                weeks_after_last_frost=2,
                succession_planting_weeks=0,
                notes="Start indoors 6 weeks before last frost, transplant 2 weeks after"
            ),
            PlantingCalendar(
                plant_type="pepper",
                weeks_before_last_frost=8,
                weeks_after_last_frost=2,
                succession_planting_weeks=0,
                notes="Start early indoors, need warm soil for transplant"
            ),
            PlantingCalendar(
                plant_type="herb",
                weeks_before_last_frost=4,
                weeks_after_last_frost=0,
                succession_planting_weeks=3,
                notes="Most herbs can be succession planted every 3 weeks"
            ),
            PlantingCalendar(
                plant_type="cucumber",
                weeks_before_last_frost=3,
                weeks_after_last_frost=2,
                succession_planting_weeks=2,
                notes="Succession plant for continuous harvest"
            ),
        ]
        
        for entry in calendar_entries:
            db.session.add(entry)
        
        print(f"Added {len(calendar_entries)} planting calendar entries")
        
        # Commit all changes
        db.session.commit()
        print("\n✅ Database initialized with sample data!")
        print("\nNext steps:")
        print("1. Start the app: python app.py")
        print("2. Visit http://localhost:5000")
        print("3. Start adding seedlings and tracking your garden!")

if __name__ == "__main__":
    init_sample_data()
