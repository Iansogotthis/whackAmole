
from flask import Flask, render_template, request, redirect, url_for
from config import Config
from app import create_app, db

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
