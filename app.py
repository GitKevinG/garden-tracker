from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from config import Config
from models import db, User, Seed, GrowBag, Seedling, Plant, Harvest, ProgressLog, PlantingCalendar, HydroSystem, HydroBag, HydroPlant, NutrientRecipe, ReservoirLog, HydroHarvest, PlantingPlan, PlantingPlanItem
from sqlalchemy import func, extract

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the garden tracker.'
login_manager.login_message_category = 'error'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# Create tables and apply migrations for new columns
with app.app_context():
    db.create_all()
    # Add hydro_bag_id column to hydro_plants if missing (SQLite doesn't alter on create_all)
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('hydro_plants')]
    if 'hydro_bag_id' not in columns:
        db.session.execute(text('ALTER TABLE hydro_plants ADD COLUMN hydro_bag_id INTEGER REFERENCES hydro_bags(id)'))
        db.session.commit()
    if 'seedling_id' not in columns:
        db.session.execute(text('ALTER TABLE hydro_plants ADD COLUMN seedling_id INTEGER REFERENCES seedlings(id)'))
        db.session.commit()
    # Add grid_row/grid_col to grow_bags if missing
    gb_columns = [c['name'] for c in inspector.get_columns('grow_bags')]
    if 'grid_row' not in gb_columns:
        db.session.execute(text('ALTER TABLE grow_bags ADD COLUMN grid_row INTEGER'))
        db.session.execute(text('ALTER TABLE grow_bags ADD COLUMN grid_col INTEGER'))
        db.session.commit()
    # Add grid_row/grid_col to hydro_systems if missing
    hs_columns = [c['name'] for c in inspector.get_columns('hydro_systems')]
    if 'grid_row' not in hs_columns:
        db.session.execute(text('ALTER TABLE hydro_systems ADD COLUMN grid_row INTEGER'))
        db.session.execute(text('ALTER TABLE hydro_systems ADD COLUMN grid_col INTEGER'))
        db.session.commit()
    user_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'tutorial_dismissed' not in user_columns:
        db.session.execute(text('ALTER TABLE users ADD COLUMN tutorial_dismissed BOOLEAN DEFAULT FALSE'))
        db.session.commit()


# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        # --- ADD THESE DEBUG LINES ---
        print(f"DEBUG: Attempting login for username: '{username}'")
        if user:
            print(f"DEBUG: User found in DB! Stored hash: {user.password_hash[:20]}...")
            match = user.check_password(password)
            print(f"DEBUG: Does password match? {match}")
        else:
            print("DEBUG: No user found with that username.")
        # -----------------------------

        if user and user.check_password(password):
            # ... rest of your code
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# Admin Routes
@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_users():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
        else:
            user = User(username=username, email=email, is_admin=False)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f'User "{username}" created successfully!', 'success')
            return redirect(url_for('admin_users'))

    users = User.query.order_by(User.created_at).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{username}" deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/create-admin-fix')
def create_admin_fix():
    # This uses the app's OWN logic to create a valid user
    try:
        # Check if 'admin' exists, if so delete it so we can start fresh
        old_user = User.query.filter_by(username='admin').first()
        if old_user:
            db.session.delete(old_user)
            db.session.commit()

        new_user = User(username='admin', email='admin@garden.com', is_admin=True)
        new_user.set_password('garden123') # This is your new temporary password
        db.session.add(new_user)
        db.session.commit()
        return "SUCCESS: User 'admin' created with password 'garden123'. Try logging in now!"
    except Exception as e:
        return f"ERROR: {str(e)}"

@app.route('/')
@login_required
def index():
    """Dashboard with overview of garden status"""
    # Get upcoming tasks
    today = datetime.now().date()

    # Seedlings ready to transplant (ready or potted_up status)
    ready_seedlings = Seedling.query.filter(
        Seedling.user_id == current_user.id,
        Seedling.status.in_(['ready', 'potted_up'])
    ).all()

    # Seedlings ready for potting up (growing status, 14+ days old)
    growing_seedlings = Seedling.query.filter_by(user_id=current_user.id, status='growing').all()
    ready_for_pot_up = [s for s in growing_seedlings if s.days_since_germination >= 14]

    # Plants approaching harvest
    upcoming_harvests = Plant.query.filter(
        Plant.user_id == current_user.id,
        Plant.expected_harvest_date.isnot(None),
        Plant.expected_harvest_date <= today + timedelta(days=14),
        Plant.expected_harvest_date >= today,
        Plant.status == 'growing'
    ).all()

    # Recent harvests (last 7 days) - filter by user through plant relationship
    week_ago = today - timedelta(days=7)
    recent_harvests = Harvest.query.join(Plant).filter(
        Plant.user_id == current_user.id,
        Harvest.harvest_date >= week_ago
    ).order_by(Harvest.harvest_date.desc()).limit(10).all()

    # Low seed inventory
    low_seeds = Seed.query.filter(Seed.user_id == current_user.id, Seed.quantity <= 10).all()

    # Active plants count
    active_plants = Plant.query.filter(
        Plant.user_id == current_user.id,
        Plant.status.in_(['growing', 'flowering', 'producing'])
    ).count()

    # Active seedlings (include potted_up)
    active_seedlings = Seedling.query.filter(
        Seedling.user_id == current_user.id,
        Seedling.status.in_(['germinating', 'growing', 'potted_up', 'ready'])
    ).count()

    # Available grow bag space
    available_space = db.session.query(
        func.sum(GrowBag.max_plants - GrowBag.current_plants)
    ).filter(GrowBag.user_id == current_user.id).scalar() or 0

    # Hydroponics data
    active_hydro_plants = HydroPlant.query.filter(
        HydroPlant.user_id == current_user.id,
        HydroPlant.status.in_(['growing', 'flowering', 'producing'])
    ).count()

    hydro_systems = HydroSystem.query.filter_by(user_id=current_user.id, status='active').all()
    reservoir_alerts = []
    ph_ec_alerts = []
    for sys in hydro_systems:
        days = sys.days_since_reservoir_change
        if days is not None and days >= 7:
            reservoir_alerts.append({'system': sys, 'days': days})
        reading = sys.latest_reading
        if reading:
            # Check recipes for target ranges
            if reading.recipe:
                r = reading.recipe
                if reading.ph_reading and r.target_ph_min and reading.ph_reading < r.target_ph_min:
                    ph_ec_alerts.append({'system': sys, 'type': 'pH Low', 'value': reading.ph_reading})
                if reading.ph_reading and r.target_ph_max and reading.ph_reading > r.target_ph_max:
                    ph_ec_alerts.append({'system': sys, 'type': 'pH High', 'value': reading.ph_reading})
                if reading.ec_reading and r.target_ec_min and reading.ec_reading < r.target_ec_min:
                    ph_ec_alerts.append({'system': sys, 'type': 'EC Low', 'value': reading.ec_reading})
                if reading.ec_reading and r.target_ec_max and reading.ec_reading > r.target_ec_max:
                    ph_ec_alerts.append({'system': sys, 'type': 'EC High', 'value': reading.ec_reading})

    show_tutorial = not current_user.tutorial_dismissed

    return render_template('dashboard.html',
                         ready_seedlings=ready_seedlings,
                         ready_for_pot_up=ready_for_pot_up,
                         upcoming_harvests=upcoming_harvests,
                         recent_harvests=recent_harvests,
                         low_seeds=low_seeds,
                         active_plants=active_plants,
                         active_seedlings=active_seedlings,
                         available_space=available_space,
                         active_hydro_plants=active_hydro_plants,
                         reservoir_alerts=reservoir_alerts,
                         ph_ec_alerts=ph_ec_alerts,
                         show_tutorial=show_tutorial,
                         today=today)


# Tutorial Routes
@app.route('/tutorial')
@login_required
def tutorial():
    """Getting started guide"""
    return render_template('tutorial.html')


@app.route('/tutorial/dismiss', methods=['POST'])
@login_required
def tutorial_dismiss():
    """Dismiss the getting started card on dashboard"""
    current_user.tutorial_dismissed = True
    db.session.commit()
    return redirect(url_for('index'))


# Seed Inventory Routes
@app.route('/seeds')
@login_required
def seeds_list():
    """List all seeds in inventory"""
    seeds = Seed.query.filter_by(user_id=current_user.id).order_by(Seed.plant_type, Seed.variety_name).all()
    return render_template('seeds/list.html', seeds=seeds)


@app.route('/seeds/add', methods=['GET', 'POST'])
@login_required
def seed_add():
    """Add new seed to inventory"""
    if request.method == 'POST':
        seed = Seed(
            user_id=current_user.id,
            variety_name=request.form['variety_name'],
            plant_type=request.form['plant_type'],
            quantity=int(request.form['quantity']),
            purchase_date=datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date() if request.form.get('purchase_date') else None,
            expiration_date=datetime.strptime(request.form['expiration_date'], '%Y-%m-%d').date() if request.form.get('expiration_date') else None,
            germination_rate=float(request.form['germination_rate']) if request.form.get('germination_rate') else None,
            supplier=request.form.get('supplier'),
            days_to_maturity=int(request.form['days_to_maturity']) if request.form.get('days_to_maturity') else None,
            weeks_to_transplant=int(request.form['weeks_to_transplant']) if request.form.get('weeks_to_transplant') else 6,
            size_category=request.form.get('size_category', 'medium'),
            notes=request.form.get('notes')
        )
        db.session.add(seed)
        db.session.commit()
        flash(f'Added {seed.variety_name} to inventory!', 'success')
        return redirect(url_for('seeds_list'))
    
    return render_template('seeds/add.html')


@app.route('/seeds/<int:seed_id>')
@login_required
def seed_detail(seed_id):
    """View seed details and performance"""
    seed = Seed.query.filter_by(id=seed_id, user_id=current_user.id).first_or_404()

    # Get all plants from this seed variety
    plants = Plant.query.filter_by(seed_id=seed_id, user_id=current_user.id).all()
    
    # Calculate variety statistics
    total_yield = sum(p.total_yield for p in plants)
    avg_yield = total_yield / len(plants) if plants else 0
    total_harvests = sum(p.harvest_count for p in plants)
    
    return render_template('seeds/detail.html', 
                         seed=seed, 
                         plants=plants,
                         total_yield=total_yield,
                         avg_yield=avg_yield,
                         total_harvests=total_harvests)


@app.route('/seeds/<int:seed_id>/delete', methods=['POST'])
@login_required
def seed_delete(seed_id):
    """Delete a seed from inventory"""
    seed = Seed.query.filter_by(id=seed_id, user_id=current_user.id).first_or_404()
    variety_name = seed.variety_name

    # Check if seed has associated plants
    if seed.plants:
        flash(f'Cannot delete {variety_name} - it has {len(seed.plants)} associated plants.', 'error')
        return redirect(url_for('seed_detail', seed_id=seed_id))

    # Check if seed has associated seedlings
    if seed.seedlings:
        flash(f'Cannot delete {variety_name} - it has {len(seed.seedlings)} associated seedlings.', 'error')
        return redirect(url_for('seed_detail', seed_id=seed_id))

    db.session.delete(seed)
    db.session.commit()
    flash(f'Deleted {variety_name} from inventory.', 'success')
    return redirect(url_for('seeds_list'))


@app.route('/seeds/<int:seed_id>/edit', methods=['GET', 'POST'])
@login_required
def seed_edit(seed_id):
    """Edit seed information"""
    seed = Seed.query.filter_by(id=seed_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        seed.variety_name = request.form['variety_name']
        seed.plant_type = request.form['plant_type']
        seed.quantity = int(request.form['quantity'])
        seed.purchase_date = datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date() if request.form.get('purchase_date') else None
        seed.expiration_date = datetime.strptime(request.form['expiration_date'], '%Y-%m-%d').date() if request.form.get('expiration_date') else None
        seed.germination_rate = float(request.form['germination_rate']) if request.form.get('germination_rate') else None
        seed.supplier = request.form.get('supplier')
        seed.days_to_maturity = int(request.form['days_to_maturity']) if request.form.get('days_to_maturity') else None
        seed.weeks_to_transplant = int(request.form['weeks_to_transplant']) if request.form.get('weeks_to_transplant') else 6
        seed.size_category = request.form.get('size_category', 'medium')
        seed.notes = request.form.get('notes')

        db.session.commit()
        flash(f'Updated {seed.variety_name}!', 'success')
        return redirect(url_for('seed_detail', seed_id=seed.id))
    
    return render_template('seeds/edit.html', seed=seed)


# Seedling Routes
@app.route('/seedlings')
@login_required
def seedlings_list():
    """List all active seedlings"""
    seedlings = Seedling.query.filter(
        Seedling.user_id == current_user.id,
        Seedling.status.in_(['germinating', 'growing', 'potted_up', 'ready'])
    ).order_by(Seedling.germination_date.desc()).all()

    return render_template('seedlings/list.html', seedlings=seedlings)


@app.route('/seedlings/add', methods=['GET', 'POST'])
@login_required
def seedling_add():
    """Start new seedlings"""
    if request.method == 'POST':
        seed_id = int(request.form['seed_id'])
        seed = Seed.query.filter_by(id=seed_id, user_id=current_user.id).first_or_404()

        sown_date = datetime.strptime(request.form['sown_date'], '%Y-%m-%d').date()
        germination_date = None
        if request.form.get('germination_date'):
            germination_date = datetime.strptime(request.form['germination_date'], '%Y-%m-%d').date()

        # Calculate expected transplant from sown date
        expected_transplant = sown_date + timedelta(weeks=seed.weeks_to_transplant)

        quantity_started = int(request.form['quantity_started'])
        quantity_viable_str = request.form.get('quantity_viable', '').strip()
        quantity_viable = int(quantity_viable_str) if quantity_viable_str else quantity_started

        # Set status based on whether germination has occurred
        status = 'growing' if germination_date else 'germinating'

        seedling = Seedling(
            user_id=current_user.id,
            seed_id=seed_id,
            sown_date=sown_date,
            germination_date=germination_date,
            quantity_started=quantity_started,
            quantity_viable=quantity_viable,
            expected_transplant_date=expected_transplant,
            location=request.form.get('location'),
            status=status,
            notes=request.form.get('notes')
        )
        
        # Update seed inventory
        seed.quantity -= seedling.quantity_started
        
        db.session.add(seedling)
        db.session.commit()
        flash(f'Started {seedling.quantity_started} {seed.variety_name} seedlings!', 'success')
        return redirect(url_for('seedlings_list'))

    seeds = Seed.query.filter(Seed.user_id == current_user.id, Seed.quantity > 0).order_by(Seed.variety_name).all()
    return render_template('seedlings/add.html', seeds=seeds)


@app.route('/seedlings/<int:seedling_id>')
@login_required
def seedling_detail(seedling_id):
    """View seedling details"""
    seedling = Seedling.query.filter_by(id=seedling_id, user_id=current_user.id).first_or_404()
    return render_template('seedlings/detail.html', seedling=seedling)


@app.route('/seedlings/<int:seedling_id>/update', methods=['POST'])
@login_required
def seedling_update(seedling_id):
    """Update seedling status"""
    seedling = Seedling.query.filter_by(id=seedling_id, user_id=current_user.id).first_or_404()

    seedling.status = request.form['status']
    quantity_viable_str = request.form.get('quantity_viable', '').strip()
    if quantity_viable_str:
        seedling.quantity_viable = int(quantity_viable_str)

    # Handle germination date recording
    if request.form.get('germination_date'):
        seedling.germination_date = datetime.strptime(request.form['germination_date'], '%Y-%m-%d').date()

    if request.form.get('notes'):
        seedling.notes = request.form['notes']

    db.session.commit()
    flash(f'Updated seedling status to {seedling.status}!', 'success')
    return redirect(url_for('seedling_detail', seedling_id=seedling.id))


@app.route('/seedlings/<int:seedling_id>/pot-up', methods=['GET', 'POST'])
@login_required
def seedling_pot_up(seedling_id):
    """Pot up seedlings to intermediate containers"""
    seedling = Seedling.query.filter_by(id=seedling_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        seedling.status = 'potted_up'
        seedling.potted_up_date = datetime.strptime(request.form['potted_up_date'], '%Y-%m-%d').date()
        seedling.pot_size = request.form.get('pot_size')
        seedling.quantity_potted_up = int(request.form.get('quantity_potted_up', seedling.quantity_viable))

        if request.form.get('notes'):
            existing_notes = seedling.notes or ''
            seedling.notes = f"{existing_notes}\n[Potted up] {request.form['notes']}".strip()

        db.session.commit()
        flash(f'Potted up {seedling.quantity_potted_up} {seedling.seed.variety_name} seedlings!', 'success')
        return redirect(url_for('seedling_detail', seedling_id=seedling.id))

    return render_template('seedlings/pot_up.html', seedling=seedling)


@app.route('/seedlings/<int:seedling_id>/delete', methods=['POST'])
@login_required
def seedling_delete(seedling_id):
    """Delete a seedling batch"""
    seedling = Seedling.query.filter_by(id=seedling_id, user_id=current_user.id).first_or_404()
    variety_name = seedling.seed.variety_name

    # Check if seedling has associated plants
    plant_count = Plant.query.filter_by(seedling_id=seedling_id).count()
    if plant_count > 0:
        flash(f'Cannot delete - {plant_count} plant(s) were created from this seedling batch.', 'error')
        return redirect(url_for('seedling_detail', seedling_id=seedling_id))

    # Optionally return seeds to inventory (for failed/deleted seedlings)
    # seedling.seed.quantity += seedling.quantity_started

    db.session.delete(seedling)
    db.session.commit()
    flash(f'Deleted {variety_name} seedling batch.', 'success')
    return redirect(url_for('seedlings_list'))


# Grow Bag Routes
@app.route('/growbags')
@login_required
def growbags_list():
    """List all grow bags"""
    growbags = GrowBag.query.filter_by(user_id=current_user.id).order_by(GrowBag.location, GrowBag.name).all()
    return render_template('growbags/list.html', growbags=growbags)


@app.route('/growbags/add', methods=['GET', 'POST'])
@login_required
def growbag_add():
    """Add new grow bag"""
    if request.method == 'POST':
        growbag = GrowBag(
            user_id=current_user.id,
            name=request.form['name'],
            size_gallons=int(request.form['size_gallons']),
            location=request.form.get('location'),
            max_plants=int(request.form['max_plants']),
            notes=request.form.get('notes')
        )
        db.session.add(growbag)
        db.session.commit()
        flash(f'Added {growbag.name}!', 'success')
        return redirect(url_for('growbags_list'))
    
    return render_template('growbags/add.html')


@app.route('/growbags/<int:growbag_id>')
@login_required
def growbag_detail(growbag_id):
    """View grow bag details and current plants"""
    growbag = GrowBag.query.filter_by(id=growbag_id, user_id=current_user.id).first_or_404()
    plants = Plant.query.filter_by(grow_bag_id=growbag_id, user_id=current_user.id).filter(
        Plant.status.in_(['growing', 'flowering', 'producing'])
    ).all()

    # Calculate capacity for each plant size category
    capacity_info = {
        'compact': growbag.get_capacity_for_size('compact'),
        'medium': growbag.get_capacity_for_size('medium'),
        'large': growbag.get_capacity_for_size('large')
    }

    return render_template('growbags/detail.html', growbag=growbag, plants=plants, capacity_info=capacity_info)


@app.route('/growbags/<int:growbag_id>/delete', methods=['POST'])
@login_required
def growbag_delete(growbag_id):
    """Delete a grow bag"""
    growbag = GrowBag.query.filter_by(id=growbag_id, user_id=current_user.id).first_or_404()
    name = growbag.name

    # Check if grow bag has active plants
    active_plants = Plant.query.filter_by(grow_bag_id=growbag_id).filter(
        Plant.status.in_(['growing', 'flowering', 'producing'])
    ).count()

    if active_plants > 0:
        flash(f'Cannot delete {name} - it has {active_plants} active plant(s). Remove plants first.', 'error')
        return redirect(url_for('growbag_detail', growbag_id=growbag_id))

    db.session.delete(growbag)
    db.session.commit()
    flash(f'Deleted {name}.', 'success')
    return redirect(url_for('growbags_list'))


# Plant Routes
@app.route('/plants')
@login_required
def plants_list():
    """List all active plants"""
    plants = Plant.query.filter(
        Plant.user_id == current_user.id,
        Plant.status.in_(['growing', 'flowering', 'producing'])
    ).order_by(Plant.transplant_date.desc()).all()

    return render_template('plants/list.html', plants=plants)


@app.route('/plants/add', methods=['GET', 'POST'])
@login_required
def plant_add():
    """Add new plant (transplant from seedling or direct)"""
    if request.method == 'POST':
        seed_id = int(request.form['seed_id'])
        seed = Seed.query.filter_by(id=seed_id, user_id=current_user.id).first_or_404()
        transplant_date = datetime.strptime(request.form['transplant_date'], '%Y-%m-%d').date()
        quantity = int(request.form.get('quantity', 1))

        # Calculate expected harvest date
        expected_harvest = seed.calculate_harvest_date(transplant_date) if seed.days_to_maturity else None

        seedling_id = int(request.form['seedling_id']) if request.form.get('seedling_id') else None
        grow_bag_id = int(request.form['grow_bag_id']) if request.form.get('grow_bag_id') else None
        base_name = request.form.get('plant_name', '')

        # Create the specified number of plants
        for i in range(quantity):
            # Generate plant name with number if creating multiple
            if quantity > 1:
                plant_name = f"{base_name} #{i+1}" if base_name else f"{seed.variety_name} #{i+1}"
            else:
                plant_name = base_name if base_name else None

            plant = Plant(
                user_id=current_user.id,
                seed_id=seed_id,
                seedling_id=seedling_id,
                grow_bag_id=grow_bag_id,
                plant_name=plant_name,
                transplant_date=transplant_date,
                expected_harvest_date=expected_harvest,
                status='growing',
                notes=request.form.get('notes')
            )
            db.session.add(plant)

        # Update grow bag plant count
        if grow_bag_id:
            growbag = GrowBag.query.get(grow_bag_id)
            growbag.current_plants += quantity

        # Update seedling - decrement available count
        if seedling_id:
            seedling = Seedling.query.get(seedling_id)
            # Use quantity_potted_up if set, otherwise quantity_viable
            available = seedling.quantity_potted_up or seedling.quantity_viable or 0
            remaining = available - quantity

            if seedling.quantity_potted_up:
                seedling.quantity_potted_up = max(0, remaining)
            else:
                seedling.quantity_viable = max(0, remaining)

            # Only mark as transplanted if all seedlings used
            if remaining <= 0:
                seedling.status = 'transplanted'
                seedling.actual_transplant_date = transplant_date

        db.session.commit()
        flash(f'Added {quantity} {seed.variety_name} plant(s) to garden!', 'success')
        return redirect(url_for('plants_list'))

    seeds = Seed.query.filter_by(user_id=current_user.id).order_by(Seed.variety_name).all()
    seedlings = Seedling.query.filter(
        Seedling.user_id == current_user.id,
        Seedling.status.in_(['ready', 'potted_up'])
    ).all()
    growbags = GrowBag.query.filter_by(user_id=current_user.id).all()

    return render_template('plants/add.html', seeds=seeds, seedlings=seedlings, growbags=growbags)


@app.route('/plants/<int:plant_id>')
@login_required
def plant_detail(plant_id):
    """View plant details, progress, and harvests"""
    plant = Plant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
    progress_logs = ProgressLog.query.filter_by(plant_id=plant_id).order_by(ProgressLog.log_date.desc()).all()
    harvests = Harvest.query.filter_by(plant_id=plant_id).order_by(Harvest.harvest_date.desc()).all()
    
    return render_template('plants/detail.html', 
                         plant=plant, 
                         progress_logs=progress_logs,
                         harvests=harvests)


# Harvest Routes
@app.route('/harvests')
@login_required
def harvests_list():
    """List all harvests"""
    harvests = Harvest.query.join(Plant).filter(
        Plant.user_id == current_user.id
    ).order_by(Harvest.harvest_date.desc()).limit(100).all()
    return render_template('harvests/list.html', harvests=harvests)


@app.route('/harvests/add', methods=['GET', 'POST'])
@login_required
def harvest_add():
    """Record a new harvest"""
    if request.method == 'POST':
        plant_id = int(request.form['plant_id'])
        plant = Plant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
        harvest_date = datetime.strptime(request.form['harvest_date'], '%Y-%m-%d').date()
        
        harvest = Harvest(
            plant_id=plant_id,
            harvest_date=harvest_date,
            amount=float(request.form['amount']),
            unit=request.form['unit'],
            quality_rating=int(request.form['quality_rating']) if request.form.get('quality_rating') else None,
            notes=request.form.get('notes')
        )
        
        # Update plant status and dates
        if not plant.first_harvest_date:
            plant.first_harvest_date = harvest_date
            plant.status = 'producing'
        plant.last_harvest_date = harvest_date
        
        db.session.add(harvest)
        db.session.commit()
        flash(f'Recorded harvest of {harvest.amount}{harvest.unit}!', 'success')
        return redirect(url_for('plant_detail', plant_id=plant_id))

    plants = Plant.query.filter(
        Plant.user_id == current_user.id,
        Plant.status.in_(['growing', 'flowering', 'producing'])
    ).all()

    return render_template('harvests/add.html', plants=plants)


# Progress Log Routes
@app.route('/plants/<int:plant_id>/log', methods=['POST'])
@login_required
def progress_log_add(plant_id):
    """Add progress log entry"""
    plant = Plant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
    
    log = ProgressLog(
        plant_id=plant_id,
        log_date=datetime.strptime(request.form['log_date'], '%Y-%m-%d').date(),
        height_inches=float(request.form['height_inches']) if request.form.get('height_inches') else None,
        growth_stage=request.form.get('growth_stage'),
        observations=request.form.get('observations'),
        issues=request.form.get('issues'),
        actions_taken=request.form.get('actions_taken')
    )
    
    # Update plant health rating if provided
    if request.form.get('health_rating'):
        plant.health_rating = int(request.form['health_rating'])
    
    db.session.add(log)
    db.session.commit()
    flash('Progress log added!', 'success')
    return redirect(url_for('plant_detail', plant_id=plant_id))


# Analytics Routes
@app.route('/analytics')
@login_required
def analytics():
    """View analytics and variety comparisons"""
    # Get variety performance data
    variety_stats = db.session.query(
        Seed.variety_name,
        Seed.plant_type,
        func.count(Plant.id).label('plant_count'),
        func.sum(Harvest.amount).label('total_yield'),
        func.avg(Harvest.quality_rating).label('avg_quality')
    ).join(Plant).join(Harvest).filter(
        Seed.user_id == current_user.id
    ).group_by(Seed.id).all()

    # Get monthly harvest totals
    monthly_harvests = db.session.query(
        extract('year', Harvest.harvest_date).label('year'),
        extract('month', Harvest.harvest_date).label('month'),
        func.sum(Harvest.amount).label('total')
    ).join(Plant).filter(
        Plant.user_id == current_user.id
    ).group_by('year', 'month').order_by('year', 'month').all()

    return render_template('analytics.html',
                         variety_stats=variety_stats,
                         monthly_harvests=monthly_harvests)


# Planting Calendar Routes
@app.route('/calendar')
@login_required
def planting_calendar():
    """View planting calendar with visual month grid"""
    import calendar as cal_module

    today = datetime.now().date()
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))

    # Calculate prev/next month for navigation
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    last_frost = Config.get_last_frost_date(year)
    first_frost = Config.get_first_frost_date(year)
    month_name = cal_module.month_name[month]

    # Build calendar grid
    cal = cal_module.Calendar(firstweekday=6)  # Start on Sunday
    weeks = cal.monthdatescalendar(year, month)

    # Initialize events dictionary
    events = {}

    def add_event(date, event_type, item):
        if date not in events:
            events[date] = {'seed_starts': [], 'transplants': [], 'harvests': []}
        events[date][event_type].append(item)

    # Get seeds with quantity > 0 and calculate their planting dates
    seeds = Seed.query.filter(Seed.user_id == current_user.id, Seed.quantity > 0).all()
    transplant_target = last_frost + timedelta(weeks=2)  # 2 weeks after last frost

    for seed in seeds:
        seed_start = seed.calculate_seed_start_date(transplant_target)
        harvest = seed.calculate_harvest_date(transplant_target)

        if seed_start:
            add_event(seed_start, 'seed_starts', {
                'name': seed.variety_name,
                'type': seed.plant_type,
                'id': seed.id
            })

        add_event(transplant_target, 'transplants', {
            'name': seed.variety_name,
            'type': seed.plant_type,
            'source': 'seed',
            'id': seed.id
        })

        if harvest:
            add_event(harvest, 'harvests', {
                'name': seed.variety_name,
                'type': seed.plant_type,
                'source': 'seed',
                'id': seed.id
            })

    # Get active seedlings and their transplant dates
    seedlings = Seedling.query.filter(
        Seedling.user_id == current_user.id,
        Seedling.status.in_(['germinating', 'growing', 'ready'])
    ).all()

    for seedling in seedlings:
        if seedling.expected_transplant_date:
            add_event(seedling.expected_transplant_date, 'transplants', {
                'name': seedling.seed.variety_name,
                'type': seedling.seed.plant_type,
                'source': 'seedling',
                'id': seedling.id,
                'quantity': seedling.quantity_viable
            })

    # Get active plants and their expected harvest dates
    plants = Plant.query.filter(
        Plant.user_id == current_user.id,
        Plant.status.in_(['growing', 'flowering', 'producing'])
    ).all()

    for plant in plants:
        if plant.expected_harvest_date:
            add_event(plant.expected_harvest_date, 'harvests', {
                'name': plant.plant_name or plant.seed_variety.variety_name,
                'type': plant.seed_variety.plant_type,
                'source': 'plant',
                'id': plant.id
            })

    # Build upcoming tasks list (next 14 days)
    upcoming_tasks = []
    for i in range(14):
        check_date = today + timedelta(days=i)
        if check_date in events:
            for seed_item in events[check_date]['seed_starts']:
                upcoming_tasks.append({
                    'date': check_date,
                    'action': 'Start Seeds',
                    'name': seed_item['name'],
                    'type': 'seed-start',
                    'badge': 'warning'
                })
            for trans_item in events[check_date]['transplants']:
                upcoming_tasks.append({
                    'date': check_date,
                    'action': 'Transplant',
                    'name': trans_item['name'],
                    'type': 'transplant',
                    'badge': 'success'
                })
            for harv_item in events[check_date]['harvests']:
                upcoming_tasks.append({
                    'date': check_date,
                    'action': 'Harvest',
                    'name': harv_item['name'],
                    'type': 'harvest',
                    'badge': 'info'
                })

    # Sort tasks by date
    upcoming_tasks.sort(key=lambda x: x['date'])

    return render_template('calendar.html',
                         weeks=weeks,
                         events=events,
                         upcoming_tasks=upcoming_tasks,
                         year=year,
                         month=month,
                         month_name=month_name,
                         prev_month=prev_month,
                         prev_year=prev_year,
                         next_month=next_month,
                         next_year=next_year,
                         last_frost=last_frost,
                         first_frost=first_frost,
                         today=today)


# API Routes
@app.route('/api/growbag-capacity')
@login_required
def api_growbag_capacity():
    """API endpoint to get capacity recommendations for transplant UI"""
    growbag_id = request.args.get('growbag_id', type=int)
    seed_id = request.args.get('seed_id', type=int)

    if not growbag_id or not seed_id:
        return jsonify({'error': 'Missing parameters'}), 400

    growbag = GrowBag.query.filter_by(id=growbag_id, user_id=current_user.id).first_or_404()
    seed = Seed.query.filter_by(id=seed_id, user_id=current_user.id).first_or_404()

    size_category = seed.size_category or 'medium'
    max_capacity = growbag.get_capacity_for_size(size_category)

    # Count current plants of similar size in this bag
    current_count = Plant.query.filter(
        Plant.grow_bag_id == growbag_id,
        Plant.status.in_(['growing', 'flowering', 'producing'])
    ).count()

    available = max(0, max_capacity - current_count)

    return jsonify({
        'growbag_name': growbag.name,
        'size_gallons': growbag.size_gallons,
        'seed_variety': seed.variety_name,
        'size_category': size_category,
        'max_capacity': max_capacity,
        'current_plants': current_count,
        'available_space': available,
        'recommendation': f"This {growbag.size_gallons}gal bag can hold {max_capacity} {size_category} plant(s). {available} space(s) available."
    })


# ========== Hydroponics Routes ==========

# --- Hydro Systems ---
@app.route('/hydro/systems')
@login_required
def hydro_systems_list():
    systems = HydroSystem.query.filter_by(user_id=current_user.id).order_by(HydroSystem.name).all()
    return render_template('hydro/systems_list.html', systems=systems)


@app.route('/hydro/systems/add', methods=['GET', 'POST'])
@login_required
def hydro_system_add():
    if request.method == 'POST':
        system = HydroSystem(
            user_id=current_user.id,
            name=request.form['name'],
            system_type=request.form.get('system_type', 'drip'),
            reservoir_size_gallons=float(request.form['reservoir_size_gallons']) if request.form.get('reservoir_size_gallons') else None,
            medium_type=request.form.get('medium_type', 'coco_coir'),
            location=request.form.get('location'),
            notes=request.form.get('notes')
        )
        db.session.add(system)
        db.session.commit()
        flash(f'Added hydro system "{system.name}"!', 'success')
        return redirect(url_for('hydro_systems_list'))
    return render_template('hydro/system_add.html')


@app.route('/hydro/systems/<int:system_id>')
@login_required
def hydro_system_detail(system_id):
    system = HydroSystem.query.filter_by(id=system_id, user_id=current_user.id).first_or_404()
    logs = ReservoirLog.query.filter_by(hydro_system_id=system_id).order_by(ReservoirLog.log_date.desc()).limit(10).all()
    plants = HydroPlant.query.filter_by(hydro_system_id=system_id).filter(
        HydroPlant.status.in_(['growing', 'flowering', 'producing'])
    ).all()
    recipes = NutrientRecipe.query.filter_by(user_id=current_user.id).order_by(NutrientRecipe.name).all()
    bags = HydroBag.query.filter_by(hydro_system_id=system_id).order_by(HydroBag.name).all()
    return render_template('hydro/system_detail.html', system=system, logs=logs, plants=plants, recipes=recipes, bags=bags)


@app.route('/hydro/systems/<int:system_id>/edit', methods=['GET', 'POST'])
@login_required
def hydro_system_edit(system_id):
    system = HydroSystem.query.filter_by(id=system_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        system.name = request.form['name']
        system.system_type = request.form.get('system_type', 'drip')
        system.reservoir_size_gallons = float(request.form['reservoir_size_gallons']) if request.form.get('reservoir_size_gallons') else None
        system.medium_type = request.form.get('medium_type', 'coco_coir')
        system.location = request.form.get('location')
        system.status = request.form.get('status', 'active')
        system.notes = request.form.get('notes')
        db.session.commit()
        flash(f'Updated "{system.name}"!', 'success')
        return redirect(url_for('hydro_system_detail', system_id=system.id))
    return render_template('hydro/system_edit.html', system=system)


@app.route('/hydro/systems/<int:system_id>/delete', methods=['POST'])
@login_required
def hydro_system_delete(system_id):
    system = HydroSystem.query.filter_by(id=system_id, user_id=current_user.id).first_or_404()
    name = system.name
    db.session.delete(system)
    db.session.commit()
    flash(f'Deleted hydro system "{name}".', 'success')
    return redirect(url_for('hydro_systems_list'))


@app.route('/hydro/systems/<int:system_id>/log', methods=['GET', 'POST'])
@login_required
def hydro_system_log(system_id):
    system = HydroSystem.query.filter_by(id=system_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        log = ReservoirLog(
            hydro_system_id=system_id,
            recipe_id=int(request.form['recipe_id']) if request.form.get('recipe_id') else None,
            log_date=datetime.strptime(request.form['log_date'], '%Y-%m-%dT%H:%M') if request.form.get('log_date') else datetime.utcnow(),
            ph_reading=float(request.form['ph_reading']) if request.form.get('ph_reading') else None,
            ec_reading=float(request.form['ec_reading']) if request.form.get('ec_reading') else None,
            ppm_reading=float(request.form['ppm_reading']) if request.form.get('ppm_reading') else None,
            water_temp=float(request.form['water_temp']) if request.form.get('water_temp') else None,
            action=request.form.get('action', 'reading'),
            amount_gallons=float(request.form['amount_gallons']) if request.form.get('amount_gallons') else None,
            notes=request.form.get('notes')
        )
        db.session.add(log)
        db.session.commit()
        flash('Reservoir log added!', 'success')
        return redirect(url_for('hydro_system_detail', system_id=system_id))
    recipes = NutrientRecipe.query.filter_by(user_id=current_user.id).order_by(NutrientRecipe.name).all()
    return render_template('hydro/system_detail.html', system=system, recipes=recipes,
                         logs=ReservoirLog.query.filter_by(hydro_system_id=system_id).order_by(ReservoirLog.log_date.desc()).limit(10).all(),
                         plants=HydroPlant.query.filter_by(hydro_system_id=system_id).filter(HydroPlant.status.in_(['growing', 'flowering', 'producing'])).all())


# --- Nutrient Recipes ---
@app.route('/hydro/recipes')
@login_required
def hydro_recipes_list():
    recipes = NutrientRecipe.query.filter_by(user_id=current_user.id).order_by(NutrientRecipe.name).all()
    return render_template('hydro/recipes_list.html', recipes=recipes)


@app.route('/hydro/recipes/add', methods=['GET', 'POST'])
@login_required
def hydro_recipe_add():
    if request.method == 'POST':
        recipe = NutrientRecipe(
            user_id=current_user.id,
            name=request.form['name'],
            nutrient_a=float(request.form['nutrient_a']) if request.form.get('nutrient_a') else None,
            nutrient_b=float(request.form['nutrient_b']) if request.form.get('nutrient_b') else None,
            epsom_salt=float(request.form['epsom_salt']) if request.form.get('epsom_salt') else None,
            target_ph_min=float(request.form['target_ph_min']) if request.form.get('target_ph_min') else None,
            target_ph_max=float(request.form['target_ph_max']) if request.form.get('target_ph_max') else None,
            target_ec_min=float(request.form['target_ec_min']) if request.form.get('target_ec_min') else None,
            target_ec_max=float(request.form['target_ec_max']) if request.form.get('target_ec_max') else None,
            growth_stage=request.form.get('growth_stage'),
            notes=request.form.get('notes')
        )
        db.session.add(recipe)
        db.session.commit()
        flash(f'Added recipe "{recipe.name}"!', 'success')
        return redirect(url_for('hydro_recipes_list'))
    return render_template('hydro/recipe_add.html')


@app.route('/hydro/recipes/<int:recipe_id>')
@login_required
def hydro_recipe_detail(recipe_id):
    recipe = NutrientRecipe.query.filter_by(id=recipe_id, user_id=current_user.id).first_or_404()
    log_count = ReservoirLog.query.filter_by(recipe_id=recipe_id).count()
    return render_template('hydro/recipe_detail.html', recipe=recipe, log_count=log_count)


@app.route('/hydro/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def hydro_recipe_edit(recipe_id):
    recipe = NutrientRecipe.query.filter_by(id=recipe_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        recipe.name = request.form['name']
        recipe.nutrient_a = float(request.form['nutrient_a']) if request.form.get('nutrient_a') else None
        recipe.nutrient_b = float(request.form['nutrient_b']) if request.form.get('nutrient_b') else None
        recipe.epsom_salt = float(request.form['epsom_salt']) if request.form.get('epsom_salt') else None
        recipe.target_ph_min = float(request.form['target_ph_min']) if request.form.get('target_ph_min') else None
        recipe.target_ph_max = float(request.form['target_ph_max']) if request.form.get('target_ph_max') else None
        recipe.target_ec_min = float(request.form['target_ec_min']) if request.form.get('target_ec_min') else None
        recipe.target_ec_max = float(request.form['target_ec_max']) if request.form.get('target_ec_max') else None
        recipe.growth_stage = request.form.get('growth_stage')
        recipe.notes = request.form.get('notes')
        db.session.commit()
        flash(f'Updated "{recipe.name}"!', 'success')
        return redirect(url_for('hydro_recipe_detail', recipe_id=recipe.id))
    return render_template('hydro/recipe_edit.html', recipe=recipe)


@app.route('/hydro/recipes/<int:recipe_id>/delete', methods=['POST'])
@login_required
def hydro_recipe_delete(recipe_id):
    recipe = NutrientRecipe.query.filter_by(id=recipe_id, user_id=current_user.id).first_or_404()
    name = recipe.name
    db.session.delete(recipe)
    db.session.commit()
    flash(f'Deleted recipe "{name}".', 'success')
    return redirect(url_for('hydro_recipes_list'))


# --- Hydro Bags ---
@app.route('/hydro/systems/<int:system_id>/bags/add', methods=['POST'])
@login_required
def hydro_bag_add(system_id):
    system = HydroSystem.query.filter_by(id=system_id, user_id=current_user.id).first_or_404()
    bag = HydroBag(
        user_id=current_user.id,
        hydro_system_id=system_id,
        name=request.form['name'],
        size_gallons=float(request.form['size_gallons']) if request.form.get('size_gallons') else None,
        medium_type=request.form.get('medium_type', 'coco_coir'),
        emitter_count=int(request.form.get('emitter_count', 1)),
        position=request.form.get('position'),
        notes=request.form.get('notes')
    )
    db.session.add(bag)
    db.session.commit()
    flash(f'Added bag "{bag.name}" to {system.name}!', 'success')
    return redirect(url_for('hydro_system_detail', system_id=system_id))


@app.route('/hydro/bags/<int:bag_id>/edit', methods=['GET', 'POST'])
@login_required
def hydro_bag_edit(bag_id):
    bag = HydroBag.query.filter_by(id=bag_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        bag.name = request.form['name']
        bag.size_gallons = float(request.form['size_gallons']) if request.form.get('size_gallons') else None
        bag.medium_type = request.form.get('medium_type', 'coco_coir')
        bag.emitter_count = int(request.form.get('emitter_count', 1))
        bag.position = request.form.get('position')
        bag.notes = request.form.get('notes')
        db.session.commit()
        flash(f'Updated bag "{bag.name}"!', 'success')
        return redirect(url_for('hydro_system_detail', system_id=bag.hydro_system_id))
    return render_template('hydro/bag_edit.html', bag=bag)


@app.route('/hydro/bags/<int:bag_id>/delete', methods=['POST'])
@login_required
def hydro_bag_delete(bag_id):
    bag = HydroBag.query.filter_by(id=bag_id, user_id=current_user.id).first_or_404()
    system_id = bag.hydro_system_id
    name = bag.name
    db.session.delete(bag)
    db.session.commit()
    flash(f'Deleted bag "{name}".', 'success')
    return redirect(url_for('hydro_system_detail', system_id=system_id))


# --- Hydro Plants ---
@app.route('/hydro/plants')
@login_required
def hydro_plants_list():
    plants = HydroPlant.query.filter_by(user_id=current_user.id).filter(
        HydroPlant.status.in_(['growing', 'flowering', 'producing'])
    ).order_by(HydroPlant.transplant_date.desc()).all()
    return render_template('hydro/plants_list.html', plants=plants)


@app.route('/hydro/plants/add', methods=['GET', 'POST'])
@login_required
def hydro_plant_add():
    if request.method == 'POST':
        seedling_id = int(request.form['seedling_id']) if request.form.get('seedling_id') else None
        transplant_date = datetime.strptime(request.form['transplant_date'], '%Y-%m-%d').date()

        plant = HydroPlant(
            user_id=current_user.id,
            hydro_system_id=int(request.form['hydro_system_id']),
            hydro_bag_id=int(request.form['hydro_bag_id']) if request.form.get('hydro_bag_id') else None,
            seed_id=int(request.form['seed_id']) if request.form.get('seed_id') else None,
            seedling_id=seedling_id,
            plant_name=request.form['plant_name'],
            transplant_date=transplant_date,
            health_rating=int(request.form['health_rating']) if request.form.get('health_rating') else None,
            notes=request.form.get('notes')
        )
        db.session.add(plant)

        # Update seedling status
        if seedling_id:
            seedling = Seedling.query.get(seedling_id)
            available = seedling.quantity_potted_up or seedling.quantity_viable or 0
            remaining = available - 1
            if seedling.quantity_potted_up:
                seedling.quantity_potted_up = max(0, remaining)
            else:
                seedling.quantity_viable = max(0, remaining)
            if remaining <= 0:
                seedling.status = 'transplanted'
                seedling.actual_transplant_date = transplant_date

        db.session.commit()
        flash(f'Added hydro plant "{plant.plant_name}"!', 'success')
        return redirect(url_for('hydro_plants_list'))
    systems = HydroSystem.query.filter_by(user_id=current_user.id, status='active').order_by(HydroSystem.name).all()
    seeds = Seed.query.filter_by(user_id=current_user.id).order_by(Seed.variety_name).all()
    bags = HydroBag.query.filter_by(user_id=current_user.id).order_by(HydroBag.name).all()
    seedlings = Seedling.query.filter(
        Seedling.user_id == current_user.id,
        Seedling.status.in_(['ready', 'potted_up'])
    ).all()
    return render_template('hydro/plant_add.html', systems=systems, seeds=seeds, bags=bags, seedlings=seedlings)


@app.route('/hydro/plants/<int:plant_id>')
@login_required
def hydro_plant_detail(plant_id):
    plant = HydroPlant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
    harvests = HydroHarvest.query.filter_by(hydro_plant_id=plant_id).order_by(HydroHarvest.harvest_date.desc()).all()
    return render_template('hydro/plant_detail.html', plant=plant, harvests=harvests)


@app.route('/hydro/plants/<int:plant_id>/edit', methods=['GET', 'POST'])
@login_required
def hydro_plant_edit(plant_id):
    plant = HydroPlant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        plant.plant_name = request.form['plant_name']
        plant.hydro_system_id = int(request.form['hydro_system_id'])
        plant.hydro_bag_id = int(request.form['hydro_bag_id']) if request.form.get('hydro_bag_id') else None
        plant.seed_id = int(request.form['seed_id']) if request.form.get('seed_id') else None
        plant.transplant_date = datetime.strptime(request.form['transplant_date'], '%Y-%m-%d').date()
        plant.status = request.form.get('status', 'growing')
        plant.health_rating = int(request.form['health_rating']) if request.form.get('health_rating') else None
        plant.notes = request.form.get('notes')
        db.session.commit()
        flash(f'Updated "{plant.plant_name}"!', 'success')
        return redirect(url_for('hydro_plant_detail', plant_id=plant.id))
    systems = HydroSystem.query.filter_by(user_id=current_user.id, status='active').order_by(HydroSystem.name).all()
    seeds = Seed.query.filter_by(user_id=current_user.id).order_by(Seed.variety_name).all()
    bags = HydroBag.query.filter_by(user_id=current_user.id).order_by(HydroBag.name).all()
    return render_template('hydro/plant_edit.html', plant=plant, systems=systems, seeds=seeds, bags=bags)


@app.route('/hydro/plants/<int:plant_id>/delete', methods=['POST'])
@login_required
def hydro_plant_delete(plant_id):
    plant = HydroPlant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
    name = plant.plant_name
    db.session.delete(plant)
    db.session.commit()
    flash(f'Deleted hydro plant "{name}".', 'success')
    return redirect(url_for('hydro_plants_list'))


# --- Hydro Harvests ---
@app.route('/hydro/harvests')
@login_required
def hydro_harvests_list():
    harvests = HydroHarvest.query.join(HydroPlant).filter(
        HydroPlant.user_id == current_user.id
    ).order_by(HydroHarvest.harvest_date.desc()).limit(100).all()
    return render_template('hydro/harvests_list.html', harvests=harvests)


@app.route('/hydro/harvests/add', methods=['GET', 'POST'])
@login_required
def hydro_harvest_add():
    if request.method == 'POST':
        plant_id = int(request.form['hydro_plant_id'])
        plant = HydroPlant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
        harvest = HydroHarvest(
            hydro_plant_id=plant_id,
            harvest_date=datetime.strptime(request.form['harvest_date'], '%Y-%m-%d').date(),
            amount=float(request.form['amount']),
            unit=request.form.get('unit', 'oz'),
            quality_rating=int(request.form['quality_rating']) if request.form.get('quality_rating') else None,
            notes=request.form.get('notes')
        )
        db.session.add(harvest)
        db.session.commit()
        flash(f'Recorded harvest of {harvest.amount}{harvest.unit}!', 'success')
        return redirect(url_for('hydro_plant_detail', plant_id=plant_id))
    plants = HydroPlant.query.filter(
        HydroPlant.user_id == current_user.id,
        HydroPlant.status.in_(['growing', 'flowering', 'producing'])
    ).all()
    return render_template('hydro/harvest_add.html', plants=plants)


# --- Reservoir Logs ---
@app.route('/hydro/logs')
@login_required
def hydro_logs_list():
    system_id = request.args.get('system_id', type=int)
    query = ReservoirLog.query.join(HydroSystem).filter(HydroSystem.user_id == current_user.id)
    if system_id:
        query = query.filter(ReservoirLog.hydro_system_id == system_id)
    logs = query.order_by(ReservoirLog.log_date.desc()).limit(100).all()
    systems = HydroSystem.query.filter_by(user_id=current_user.id).order_by(HydroSystem.name).all()
    return render_template('hydro/logs_list.html', logs=logs, systems=systems, selected_system_id=system_id)


# ========== Garden Layout Routes ==========

@app.route('/garden/layout')
@login_required
def garden_layout():
    growbags = GrowBag.query.filter_by(user_id=current_user.id).all()
    hydro_systems = HydroSystem.query.filter_by(user_id=current_user.id).all()

    # Collect all unique locations (zones)
    zones = set()
    for gb in growbags:
        zones.add(gb.location or 'Unassigned')
    for hs in hydro_systems:
        zones.add(hs.location or 'Unassigned')
    if not zones:
        zones.add('Unassigned')
    zones = sorted(zones)

    # Build placed/unplaced lists
    placed = []
    unplaced = []
    for gb in growbags:
        item = {
            'type': 'growbag', 'id': gb.id, 'name': gb.name,
            'size': gb.size_gallons, 'zone': gb.location or 'Unassigned',
            'row': gb.grid_row, 'col': gb.grid_col,
            'plants': gb.current_plants, 'capacity': gb.max_plants,
            'is_full': gb.is_full, 'url': url_for('growbag_detail', growbag_id=gb.id)
        }
        if gb.grid_row is not None and gb.grid_col is not None:
            placed.append(item)
        else:
            unplaced.append(item)
    for hs in hydro_systems:
        item = {
            'type': 'hydro', 'id': hs.id, 'name': hs.name,
            'size': hs.reservoir_size_gallons, 'zone': hs.location or 'Unassigned',
            'row': hs.grid_row, 'col': hs.grid_col,
            'plants': hs.active_plant_count, 'capacity': hs.total_bags or '-',
            'is_full': False, 'url': url_for('hydro_system_detail', system_id=hs.id)
        }
        if hs.grid_row is not None and hs.grid_col is not None:
            placed.append(item)
        else:
            unplaced.append(item)

    return render_template('garden/layout.html', zones=zones, placed=placed, unplaced=unplaced)


@app.route('/garden/layout/update', methods=['POST'])
@login_required
def garden_layout_update():
    data = request.get_json()
    item_type = data.get('type')
    item_id = data.get('id')
    row = data.get('row')
    col = data.get('col')

    if row is None or col is None or not (0 <= row <= 7 and 0 <= col <= 7):
        return jsonify({'ok': False, 'error': 'Invalid grid position'}), 400

    if item_type == 'growbag':
        obj = GrowBag.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    elif item_type == 'hydro':
        obj = HydroSystem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    else:
        return jsonify({'ok': False, 'error': 'Invalid type'}), 400

    obj.grid_row = row
    obj.grid_col = col
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/garden/layout/remove', methods=['POST'])
@login_required
def garden_layout_remove():
    data = request.get_json()
    item_type = data.get('type')
    item_id = data.get('id')

    if item_type == 'growbag':
        obj = GrowBag.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    elif item_type == 'hydro':
        obj = HydroSystem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    else:
        return jsonify({'ok': False, 'error': 'Invalid type'}), 400

    obj.grid_row = None
    obj.grid_col = None
    db.session.commit()
    return jsonify({'ok': True})


# ========== Planting Plan Routes ==========

@app.route('/planner')
@login_required
def planner_list():
    plans = PlantingPlan.query.filter_by(user_id=current_user.id).order_by(PlantingPlan.updated_at.desc()).all()
    return render_template('planner/list.html', plans=plans)


@app.route('/planner/new', methods=['GET', 'POST'])
@login_required
def planner_new():
    if request.method == 'POST':
        plan = PlantingPlan(
            user_id=current_user.id,
            name=request.form['name'],
            bag_size_gallons=int(request.form.get('bag_size_gallons', 10)),
            notes=request.form.get('notes')
        )
        db.session.add(plan)
        db.session.commit()
        flash(f'Created plan "{plan.name}"!', 'success')
        return redirect(url_for('planner_detail', id=plan.id))
    return render_template('planner/new.html')


@app.route('/planner/<int:id>')
@login_required
def planner_detail(id):
    plan = PlantingPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    seeds = Seed.query.filter_by(user_id=current_user.id).order_by(Seed.plant_type, Seed.variety_name).all()
    last_frost = Config.get_last_frost_date()

    # Group items by plant_type
    groups = {}
    for item in plan.items:
        pt = item.seed.plant_type
        if pt not in groups:
            groups[pt] = []
        groups[pt].append(item)

    # Build seed start schedule
    schedule = {}
    for item in plan.items:
        start_date = item.get_seed_start_date(last_frost)
        if start_date not in schedule:
            schedule[start_date] = []
        schedule[start_date].append(item)
    schedule = dict(sorted(schedule.items()))

    return render_template('planner/detail.html', plan=plan, seeds=seeds,
                         groups=groups, schedule=schedule, last_frost=last_frost)


@app.route('/planner/<int:id>/add-item', methods=['POST'])
@login_required
def planner_add_item(id):
    plan = PlantingPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    seed_id = int(request.form['seed_id'])
    seed = Seed.query.filter_by(id=seed_id, user_id=current_user.id).first_or_404()

    plants_per_bag = request.form.get('plants_per_bag')
    if plants_per_bag:
        plants_per_bag = int(plants_per_bag)
    else:
        plants_per_bag = GrowBag.calculate_capacity(plan.bag_size_gallons, seed.size_category)

    item = PlantingPlanItem(
        plan_id=plan.id,
        seed_id=seed_id,
        num_bags=int(request.form['num_bags']),
        plants_per_bag=plants_per_bag,
        is_direct_sow='is_direct_sow' in request.form,
        notes=request.form.get('notes')
    )
    db.session.add(item)
    db.session.commit()
    flash(f'Added {seed.variety_name} to plan!', 'success')
    return redirect(url_for('planner_detail', id=plan.id))


@app.route('/planner/<int:id>/remove-item/<int:item_id>', methods=['POST'])
@login_required
def planner_remove_item(id, item_id):
    plan = PlantingPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    item = PlantingPlanItem.query.filter_by(id=item_id, plan_id=plan.id).first_or_404()
    variety = item.seed.variety_name
    db.session.delete(item)
    db.session.commit()
    flash(f'Removed {variety} from plan.', 'success')
    return redirect(url_for('planner_detail', id=plan.id))


@app.route('/planner/<int:id>/delete', methods=['POST'])
@login_required
def planner_delete(id):
    plan = PlantingPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    name = plan.name
    db.session.delete(plan)
    db.session.commit()
    flash(f'Deleted plan "{name}".', 'success')
    return redirect(url_for('planner_list'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
