from datetime import datetime, timedelta
from math import ceil
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
    tutorial_dismissed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to user's data
    seeds = db.relationship('Seed', backref='owner', lazy=True)
    grow_bags = db.relationship('GrowBag', backref='owner', lazy=True)
    seedlings = db.relationship('Seedling', backref='owner', lazy=True)
    plants = db.relationship('Plant', backref='owner', lazy=True)
    hydro_systems = db.relationship('HydroSystem', backref='owner', lazy=True)
    nutrient_recipes = db.relationship('NutrientRecipe', backref='owner', lazy=True)
    hydro_plants = db.relationship('HydroPlant', backref='owner', lazy=True)
    hydro_bags = db.relationship('HydroBag', backref='owner', lazy=True)
    planting_plans = db.relationship('PlantingPlan', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if check_password_hash(self.password_hash, password):
            return True
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
    grid_row = db.Column(db.Integer)
    grid_col = db.Column(db.Integer)
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


class HydroSystem(db.Model):
    """Track hydroponic systems"""
    __tablename__ = 'hydro_systems'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    system_type = db.Column(db.String(20), default='drip')  # drip/dwc/nft/kratky
    reservoir_size_gallons = db.Column(db.Float)
    medium_type = db.Column(db.String(30), default='coco_coir')  # coco_coir/perlite/mixed/clay_pebbles
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active/inactive/maintenance
    grid_row = db.Column(db.Integer)
    grid_col = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    hydro_plants = db.relationship('HydroPlant', backref='system', lazy=True, cascade='all, delete-orphan')
    reservoir_logs = db.relationship('ReservoirLog', backref='system', lazy=True, cascade='all, delete-orphan')
    hydro_bags = db.relationship('HydroBag', backref='system', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<HydroSystem {self.name}>'

    @property
    def total_bags(self):
        return len(self.hydro_bags)

    @property
    def total_emitters(self):
        return sum(b.emitter_count for b in self.hydro_bags)

    @property
    def active_plant_count(self):
        return sum(1 for p in self.hydro_plants if p.status in ['growing', 'flowering', 'producing'])

    @property
    def days_since_reservoir_change(self):
        changes = [log for log in self.reservoir_logs if log.action == 'full_change']
        if changes:
            latest = max(changes, key=lambda l: l.log_date)
            return (datetime.utcnow() - latest.log_date).days
        return None

    @property
    def latest_reading(self):
        if self.reservoir_logs:
            return max(self.reservoir_logs, key=lambda l: l.log_date)
        return None


class HydroBag(db.Model):
    """Track grow bags within a hydro system with drip emitter tracking"""
    __tablename__ = 'hydro_bags'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hydro_system_id = db.Column(db.Integer, db.ForeignKey('hydro_systems.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    size_gallons = db.Column(db.Float)
    medium_type = db.Column(db.String(30), default='coco_coir')
    emitter_count = db.Column(db.Integer, default=1)
    position = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    hydro_plants = db.relationship('HydroPlant', backref='hydro_bag', lazy=True)

    def __repr__(self):
        return f'<HydroBag {self.name}>'

    @property
    def active_plant_count(self):
        return sum(1 for p in self.hydro_plants if p.status in ['growing', 'flowering', 'producing'])


class HydroPlant(db.Model):
    """Track plants in hydroponic systems"""
    __tablename__ = 'hydro_plants'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hydro_system_id = db.Column(db.Integer, db.ForeignKey('hydro_systems.id'), nullable=False)
    hydro_bag_id = db.Column(db.Integer, db.ForeignKey('hydro_bags.id'), nullable=True)
    seed_id = db.Column(db.Integer, db.ForeignKey('seeds.id'), nullable=True)
    seedling_id = db.Column(db.Integer, db.ForeignKey('seedlings.id'), nullable=True)
    plant_name = db.Column(db.String(100), nullable=False)
    transplant_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='growing')  # growing/flowering/producing/removed/dead
    health_rating = db.Column(db.Integer)  # 1-10
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    hydro_harvests = db.relationship('HydroHarvest', backref='hydro_plant', lazy=True, cascade='all, delete-orphan')
    seed = db.relationship('Seed', backref='hydro_plants')
    seedling = db.relationship('Seedling', backref='hydro_plants')

    def __repr__(self):
        return f'<HydroPlant {self.plant_name}>'

    @property
    def days_since_transplant(self):
        if self.transplant_date:
            return (datetime.now().date() - self.transplant_date).days
        return 0

    @property
    def total_yield(self):
        return sum(h.amount for h in self.hydro_harvests)


class NutrientRecipe(db.Model):
    """Track nutrient mix recipes for hydroponics"""
    __tablename__ = 'nutrient_recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    nutrient_a = db.Column(db.Float)  # g per gallon
    nutrient_b = db.Column(db.Float)  # g per gallon
    epsom_salt = db.Column(db.Float)  # g per gallon
    target_ph_min = db.Column(db.Float)
    target_ph_max = db.Column(db.Float)
    target_ec_min = db.Column(db.Float)
    target_ec_max = db.Column(db.Float)
    growth_stage = db.Column(db.String(30))  # seedling/vegetative/flowering/fruiting
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<NutrientRecipe {self.name}>'


class ReservoirLog(db.Model):
    """Track reservoir readings and changes"""
    __tablename__ = 'reservoir_logs'

    id = db.Column(db.Integer, primary_key=True)
    hydro_system_id = db.Column(db.Integer, db.ForeignKey('hydro_systems.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('nutrient_recipes.id'), nullable=True)
    log_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ph_reading = db.Column(db.Float)
    ec_reading = db.Column(db.Float)
    ppm_reading = db.Column(db.Float)
    water_temp = db.Column(db.Float)
    action = db.Column(db.String(20), default='reading')  # reading/top_off/full_change/nutrient_add
    amount_gallons = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    recipe = db.relationship('NutrientRecipe', backref='reservoir_logs')

    def __repr__(self):
        return f'<ReservoirLog {self.action} on {self.log_date}>'


class HydroHarvest(db.Model):
    """Track harvests from hydroponic plants"""
    __tablename__ = 'hydro_harvests'

    id = db.Column(db.Integer, primary_key=True)
    hydro_plant_id = db.Column(db.Integer, db.ForeignKey('hydro_plants.id'), nullable=False)
    harvest_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), default='oz')
    quality_rating = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<HydroHarvest {self.amount}{self.unit} on {self.harvest_date}>'


class PlantingPlan(db.Model):
    """Saved planting plans with bag allocations"""
    __tablename__ = 'planting_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    bag_size_gallons = db.Column(db.Integer, default=10)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('PlantingPlanItem', backref='plan', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PlantingPlan {self.name}>'

    @property
    def total_bags(self):
        return sum(item.num_bags for item in self.items)

    @property
    def total_seeds_needed(self):
        return sum(item.seeds_to_start for item in self.items)


class PlantingPlanItem(db.Model):
    """Individual variety allocation within a planting plan"""
    __tablename__ = 'planting_plan_items'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('planting_plans.id', ondelete='CASCADE'), nullable=False)
    seed_id = db.Column(db.Integer, db.ForeignKey('seeds.id'), nullable=False)
    num_bags = db.Column(db.Integer, nullable=False)
    plants_per_bag = db.Column(db.Integer, nullable=False)
    is_direct_sow = db.Column(db.Boolean, default=False)
    notes = db.Column(db.String(200))

    seed = db.relationship('Seed', backref='plan_items')

    def __repr__(self):
        return f'<PlantingPlanItem {self.seed.variety_name} x{self.num_bags}>'

    @property
    def total_plants_needed(self):
        return self.num_bags * self.plants_per_bag

    @property
    def seeds_to_start(self):
        total = self.total_plants_needed
        if self.seed.germination_rate and self.seed.germination_rate > 0:
            return ceil(total / (self.seed.germination_rate / 100))
        return total * 2

    def get_seed_start_date(self, last_frost_date):
        if self.is_direct_sow:
            return last_frost_date + timedelta(weeks=2)
        weeks = self.seed.weeks_to_transplant or 6
        return last_frost_date - timedelta(weeks=weeks)
