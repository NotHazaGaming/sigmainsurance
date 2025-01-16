from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# File to store users
USERS_FILE = 'users.json'

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

        # Load users
        users = load_users()

        if email in users and users[email]['password'] == password:
            return jsonify({
                'valid': True, 
                'loyalty_card': users[email]['loyalty_card']
            })
        return jsonify({'valid': False})
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'valid': False})

@app.route('/calculate-hire', methods=['POST'])
def calculate_hire():
    data = request.json
    vehicle_type = data.get('vehicleType')
    days = int(data.get('days', 0))
    insurance = data.get('insurance')
    loyalty_card = data.get('loyaltyCard')

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

# Admin route to view users (remove in production)
@app.route('/admin/users')
def view_users():
    users = load_users()
    return jsonify(users)

if __name__ == '__main__':
    app.run()