from flask import Flask, request, jsonify
import json
import os
import re

app = Flask(__name__)

# File to store users
USERS_FILE = 'users.json'

# Validation patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PASSWORD_LENGTH = 8
PASSWORD_PATTERN = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'

# Initialize empty users file if it doesn't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def is_valid_email(email):
    return re.match(EMAIL_PATTERN, email) is not None

def is_valid_password(password):
    if len(password) < PASSWORD_LENGTH:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[@$!%*#?&]', password):
        return False, "Password must contain at least one special character (@$!%*#?&)"
    
    return True, "Password is valid"

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
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'})

        # Validate email format
        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format. Please use a valid email address'})

        # Validate password
        is_valid, password_message = is_valid_password(password)
        if not is_valid:
            return jsonify({'success': False, 'message': password_message})

        # Load existing users
        users = load_users()
        
        if email in users:
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Add new user
        users[email] = {
            'password': password,
            'loyalty_card': 'bronze'
        }
        
        # Save updated users
        save_users(users)
        
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