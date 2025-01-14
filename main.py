
from flask import Flask, render_template
from app import create_app, db

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
