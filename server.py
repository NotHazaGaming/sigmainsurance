from flask import Flask, render_template

# Create the Flask app
app = Flask(__name__)

# Define routes
@app.route('/')
def home():
    return render_template('index.html')

# Only if running directly (not through Gunicorn)
if __name__ == '__main__':
    app.run() 