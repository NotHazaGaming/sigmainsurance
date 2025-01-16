from flask import Flask, request, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

# File paths
USERS_FILE = 'users.json'
BACKUP_DIR = 'backups'

# Ensure backup directory exists
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def backup_users():
    """Backup users before each deployment"""
    if os.path.exists(USERS_FILE):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'{BACKUP_DIR}/users_backup_{timestamp}.json'
        with open(USERS_FILE, 'r') as source:
            users = json.load(source)
            with open(backup_file, 'w') as target:
                json.dump(users, target, indent=2)
        return users
    return {}

def restore_users():
    """Restore users from most recent backup"""
    backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith('users_backup_')]
    if backup_files:
        latest_backup = max(backup_files)
        with open(f'{BACKUP_DIR}/{latest_backup}', 'r') as f:
            users = json.load(f)
            with open(USERS_FILE, 'w') as target:
                json.dump(users, target, indent=2)
            return users
    return {}

# Initialize or restore users
if not os.path.exists(USERS_FILE):
    users = restore_users()
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

@app.route('/')
def home():
    with open('index.html', 'r') as f:
        return f.read()

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        
        if email in users:
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        users[email] = {
            'password': password,
            'loyalty_card': 'bronze'
        }
        
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        
        # Create backup after registration
        backup_users()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'success': False, 'message': f'Registration error: {str(e)}'})

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        # Validate email format
        if not is_valid_email(email):
            return jsonify({'valid': False, 'message': 'Invalid email format'})

        # Load users
        users = load_users()

        if email in users and users[email]['password'] == password:
            return jsonify({
                'valid': True, 
                'loyalty_card': users[email]['loyalty_card']
            })
        return jsonify({'valid': False, 'message': 'Invalid email or password'})
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'valid': False, 'message': 'Login failed'})

@app.route('/calculate-hire', methods=['POST'])
def calculate_hire():
    data = request.json
    vehicle_type = data.get('vehicleType')
    days = int(data.get('days', 0))
    insurance = data.get('insurance')
    loyalty_card = data.get('loyaltyCard', None)  # Optional now

    # Daily charges
    daily_charges = {'S': 22.50, 'HP': 28.00, 'V': 35.00}
    daily_charge = daily_charges[vehicle_type]

    # Calculate total cost
    total_cost = daily_charge * days

    # Apply discounts only for logged-in users with loyalty cards
    if loyalty_card:
        if days > 7:
            total_cost *= 0.9  # 10% discount
        if loyalty_card == 'gold' and vehicle_type == 'HP':
            total_cost -= 18.00

    # Add insurance if required
    if insurance == 'yes':
        total_cost += 15.50

    # Add deposit
    total_cost += 50.00

    return jsonify({
        'totalCost': round(total_cost, 2),
        'discounts': [
            "10% discount for hire period over 7 days" if days > 7 and loyalty_card else None,
            "£18 discount for Gold loyalty card" if loyalty_card == 'gold' and vehicle_type == 'HP' else None
        ]
    })

# Admin route to view users (remove in production)
@app.route('/admin/users')
def view_users():
    users = load_users()
    return jsonify(users)

if __name__ == '__main__':
    app.run()