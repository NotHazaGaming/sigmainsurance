from flask import Flask, request, jsonify
import os
import psycopg2
from psycopg2.extras import DictCursor
from urllib.parse import urlparse

app = Flask(__name__)

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/vehicle_hire')

# Update URL for newer versions of psycopg2
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create users table if it doesn't exist
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            loyalty_card TEXT DEFAULT 'bronze'
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

# Initialize database
init_db()

@app.route('/')
def home():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'})

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute('SELECT email FROM users WHERE email = %s', (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Insert new user
        cur.execute(
            'INSERT INTO users (email, password, loyalty_card) VALUES (%s, %s, %s)',
            (email, password, 'bronze')
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
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

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        
        cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cur.fetchone()
        
        cur.close()
        conn.close()

        if user:
            return jsonify({
                'valid': True,
                'loyalty_card': user['loyalty_card']
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
    loyalty_card = data.get('loyaltyCard', None)

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

@app.route('/admin/users')
def view_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute('SELECT email, loyalty_card FROM users')
        users = {row['email']: {'loyalty_card': row['loyalty_card']} for row in cur.fetchall()}
        cur.close()
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()