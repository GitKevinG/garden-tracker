from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User accounts for multi-user support"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to user's data
    seeds = db.relationship('Seed', backref='owner', lazy=True)
    grow_bags = db.relationship('GrowBag', backref='owner', lazy=True)
    seedlings = db.relationship('Seedling', backref='owner', lazy=True)
    plants = db.relationship('Plant', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
    # This stops looking for a hash and just compares the strings
        return self.password_hash == password

    def __repr__(self):
        return f'<User {self.username}>'

class Seed(db.Model):
    """Track seed inventory"""
    __tablename__ = 'seeds'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    variety_name = db.Column(db.String(100), nullable=False)
    plant_type = db.Column(db.String(50), nullable=False)  # tomato, pepper, etc.
    quantity = db.Column(db.Integer, default=0)
    purchase_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date)
    germination_rate = db.Column(db.Float)  # percentage
    supplier = db.Column(db.String(100))
    days_to_maturity = db.Column(db.Integer)  # days from transplant to harvest
    weeks_to_transplant = db.Column(db.Integer, default=6)  # weeks from seed to transplant
    size_category = db.Column(db.String(20), default='medium')  # compact, medium, large
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    plants = db.relationship('Plant', backref='seed_variety', lazy=True)
    
    def __repr__(self):
        return f'<Seed {self.variety_name}>'
    
    def calculate_seed_start_date(self, transplant_date):
        """Calculate when to start seeds based on transplant date"""
        weeks_before = self.weeks_to_transplant or 6
        return transplant_date - timedelta(weeks=weeks_before)
    
    def calculate_harvest_date(self, transplant_date):
        """Calculate expected harvest date"""
        if self.days_to_maturity:
            return transplant_date + timedelta(days=self.days_to_maturity)
        return None

    @property
    def spacing_inches(self):
        """Return recommended spacing in inches based on size category"""
        return {'compact': 6, 'medium': 15, 'large': 30}.get(self.size_category, 15)


class GrowBag(db.Model):
    """Track grow bags/containers"""
    __tablename__ = 'grow_bags'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    size_gallons = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100))  # balcony, deck, etc.
    max_plants = db.Column(db.Integer, default=1)
    current_plants = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    plants = db.relationship('Plant', backref='container', lazy=True)
    
    def __repr__(self):
        return f'<GrowBag {self.name} ({self.size_gallons}gal)>'
    
    @property
    def is_full(self):
        return self.current_plants >= self.max_plants
    
    @property
    def available_space(self):
        return self.max_plants - self.current_plants

    @staticmethod
    def calculate_capacity(size_gallons, plant_size_category):
        """Calculate how many plants of a given size fit in a bag"""
        capacity = {
            'compact': {1: 1, 2: 2, 3: 3, 5: 5, 7: 7, 10: 10, 15: 15, 20: 20, 25: 25},
            'medium':  {1: 0, 2: 0, 3: 1, 5: 1, 7: 2, 10: 2, 15: 3, 20: 4, 25: 5},
            'large':   {1: 0, 2: 0, 3: 0, 5: 0, 7: 1, 10: 1, 15: 1, 20: 2, 25: 2}
        }
        size_map = capacity.get(plant_size_category, capacity['medium'])
        sizes = sorted(size_map.keys())
        for size in sizes:
            if size_gallons <= size:
                return size_map[size]
        return size_map[max(sizes)]

    def get_capacity_for_size(self, plant_size_category):
        """Get capacity for a specific plant size category"""
        return GrowBag.calculate_capacity(self.size_gallons, plant_size_category)


class Seedling(db.Model):
    """Track seedlings from germination to transplant"""
    __tablename__ = 'seedlings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seed_id = db.Column(db.Integer, db.ForeignKey('seeds.id'), nullable=False)
    sown_date = db.Column(db.Date)  # when seeds were planted
    germination_date = db.Column(db.Date)  # when seeds sprouted
    quantity_started = db.Column(db.Integer, default=1)
    quantity_viable = db.Column(db.Integer)
    expected_transplant_date = db.Column(db.Date)
    actual_transplant_date = db.Column(db.Date)
    potted_up_date = db.Column(db.Date)  # when seedlings were potted up
    pot_size = db.Column(db.String(20))  # e.g., "3 inch", "4 inch", "6 inch"
    quantity_potted_up = db.Column(db.Integer)  # how many were potted up
    location = db.Column(db.String(100))  # indoor location while growing
    status = db.Column(db.String(20), default='germinating')  # germinating, growing, potted_up, ready, transplanted, failed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    seed = db.relationship('Seed', backref='seedlings')
    
    def __repr__(self):
        return f'<Seedling {self.seed.variety_name} - {self.status}>'
    
    @property
    def days_since_sown(self):
        if self.sown_date:
            return (datetime.now().date() - self.sown_date).days
        return 0

    @property
    def days_since_germination(self):
        if self.germination_date:
            return (datetime.now().date() - self.germination_date).days
        return 0

    @property
    def days_to_germinate(self):
        """Days from sowing to germination"""
        if self.sown_date and self.germination_date:
            return (self.germination_date - self.sown_date).days
        return None
    
    @property
    def days_until_transplant(self):
        if self.expected_transplant_date:
            return (self.expected_transplant_date - datetime.now().date()).days
        return None

    @property
    def days_since_potted_up(self):
        """Days since potted up (if applicable)"""
        if self.potted_up_date:
            return (datetime.now().date() - self.potted_up_date).days
        return None


class Plant(db.Model):
    """Track individual plants in grow bags"""
    __tablename__ = 'plants'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seed_id = db.Column(db.Integer, db.ForeignKey('seeds.id'), nullable=False)
    seedling_id = db.Column(db.Integer, db.ForeignKey('seedlings.id'))
    grow_bag_id = db.Column(db.Integer, db.ForeignKey('grow_bags.id'))
    plant_name = db.Column(db.String(100))  # custom name for this specific plant
    transplant_date = db.Column(db.Date, nullable=False)
    expected_harvest_date = db.Column(db.Date)
    first_harvest_date = db.Column(db.Date)
    last_harvest_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='growing')  # growing, flowering, producing, dormant, dead
    health_rating = db.Column(db.Integer)  # 1-10 scale
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    harvests = db.relationship('Harvest', backref='plant', lazy=True, cascade='all, delete-orphan')
    progress_logs = db.relationship('ProgressLog', backref='plant', lazy=True, cascade='all, delete-orphan')
    seedling = db.relationship('Seedling', backref='plants')
    
    def __repr__(self):
        return f'<Plant {self.plant_name or self.seed_variety.variety_name}>'
    
    @property
    def days_since_transplant(self):
        if self.transplant_date:
            return (datetime.now().date() - self.transplant_date).days
        return 0
    
    @property
    def total_yield(self):
        return sum(h.amount for h in self.harvests)
    
    @property
    def harvest_count(self):
        return len(self.harvests)


class Harvest(db.Model):
    """Track harvest yields"""
    __tablename__ = 'harvests'
    
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=False)
    harvest_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)  # weight in ounces or count
    unit = db.Column(db.String(20), default='oz')  # oz, lbs, count
    quality_rating = db.Column(db.Integer)  # 1-10 scale
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Harvest {self.amount}{self.unit} on {self.harvest_date}>'


class ProgressLog(db.Model):
    """Track plant progress over time"""
    __tablename__ = 'progress_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=False)
    log_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    height_inches = db.Column(db.Float)
    growth_stage = db.Column(db.String(50))  # seedling, vegetative, flowering, fruiting
    observations = db.Column(db.Text)
    issues = db.Column(db.Text)  # pests, diseases, deficiencies
    actions_taken = db.Column(db.Text)  # fertilized, pruned, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProgressLog {self.plant.plant_name} - {self.log_date}>'


class PlantingCalendar(db.Model):
    """Pre-defined planting schedules for varieties"""
    __tablename__ = 'planting_calendar'
    
    id = db.Column(db.Integer, primary_key=True)
    plant_type = db.Column(db.String(50), nullable=False)
    variety_name = db.Column(db.String(100))
    weeks_before_last_frost = db.Column(db.Integer)  # when to start seeds indoors (negative = after)
    weeks_after_last_frost = db.Column(db.Integer)  # when to transplant outdoors (negative = before)
    succession_planting_weeks = db.Column(db.Integer)  # how often to start new seeds for continuous harvest
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PlantingCalendar {self.plant_type}>'
    
    def calculate_seed_start_date(self, last_frost_date):
        """Calculate when to start seeds indoors"""
        weeks = self.weeks_before_last_frost or 0
        return last_frost_date - timedelta(weeks=abs(weeks))
    
    def calculate_transplant_date(self, last_frost_date):
        """Calculate when to transplant outdoors"""
        weeks = self.weeks_after_last_frost or 0
        if weeks < 0:
            return last_frost_date - timedelta(weeks=abs(weeks))
        return last_frost_date + timedelta(weeks=weeks)
