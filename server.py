from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Database connection
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(database_url)

# Initialize database
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS hire_quotes
        (email TEXT PRIMARY KEY,
         vehicle_type TEXT,
         days INTEGER,
         insurance TEXT,
         loyalty_card TEXT,
         total_cost FLOAT)
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.before_first_request
def setup():
    init_db()

@app.route('/')
def home():
    with open('index.html', 'r') as f:
        return f.read()

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

    # Save to database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO hire_quotes 
            (email, vehicle_type, days, insurance, loyalty_card, total_cost)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
            vehicle_type = EXCLUDED.vehicle_type,
            days = EXCLUDED.days,
            insurance = EXCLUDED.insurance,
            loyalty_card = EXCLUDED.loyalty_card,
            total_cost = EXCLUDED.total_cost
        ''', (email, vehicle_type, days, insurance, loyalty_card, total_cost))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Failed to save quote'}), 500

    return jsonify({
        'totalCost': round(total_cost, 2),
        'discounts': [
            "10% discount for hire period over 7 days" if days > 7 else None,
            "£18 discount for Gold loyalty card" if loyalty_card == 'gold' and vehicle_type == 'HP' else None
        ]
    })

@app.route('/check-email', methods=['POST'])
def check_email():
    email = request.json.get('email')
    if not email:
        return jsonify({'exists': False})
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT loyalty_card FROM hire_quotes WHERE email = %s', (email,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            'exists': result is not None,
            'loyaltyCard': result[0] if result else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run() 