from flask import Flask, request, jsonify

app = Flask(__name__)

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
    # For now, always return as new customer
    return jsonify({
        'exists': False,
        'loyaltyCard': None
    })

if __name__ == '__main__':
    app.run() 