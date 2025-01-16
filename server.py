from flask import Flask

# Create the Flask app
app = Flask(__name__)

# Define routes
@app.route('/')
def home():
    with open('index.html', 'r') as f:
        return f.read()

# Only if running directly (not through Gunicorn)
if __name__ == '__main__':
    app.run() 