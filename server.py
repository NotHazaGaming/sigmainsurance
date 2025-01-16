from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# File to store user credentials
USERS_FILE = 'users.json'

# Initialize users file if it doesn't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

def save_user(email, password):
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        users[email] = {'password': password, 'loyalty_card': 'bronze'}  # New users start with bronze
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
        return True
    except Exception as e:
        print(f"Error saving user: {e}")
        return False

def check_user(email, password):
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        if email in users and users[email]['password'] == password:
            return {'valid': True, 'loyalty_card': users[email]['loyalty_card']}
        return {'valid': False}
    except Exception as e:
        print(f"Error checking user: {e}")
        return {'valid': False}

@app.route('/')
def home():
    with open('index.html', 'r') as f:
        return f.read()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    # Check if user already exists
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    if email in users:
        return jsonify({'success': False, 'message': 'Email already registered'})
    
    if save_user(email, password):
        return jsonify({'success': True, 'message': 'Registration successful'})
    return jsonify({'success': False, 'message': 'Registration failed'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    result = check_user(data.get('email'), data.get('password'))
    return jsonify(result)

@app.route('/calculate-hire', methods=['POST'])
def calculate_hire():
    data = request.json
    vehicle_type = data.get('vehicleType')
    days = int(data.get('days', 0))
    insurance = data.get('insurance')
    loyalty_card = data.get('loyaltyCard')
    email = data.get('email')

    # Daily charges
    daily_charges = {'S': 22.50, 'HP': 28.00, 'V': 35.00}
    daily_charge = daily_charges[vehicle_type]

    # Calculate total cost
    total_cost = daily_charge * days

    # Apply discounts
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
            "10% discount for hire period over 7 days" if days > 7 else None,
            "£18 discount for Gold loyalty card" if loyalty_card == 'gold' and vehicle_type == 'HP' else None
        ]
    })

if __name__ == '__main__':
    app.run() 