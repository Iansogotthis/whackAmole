import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response, session
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from config import Config
from sqlalchemy import func, text
import json
import time
from urllib.parse import urlparse, urljoin
from models import db, User, HighScore, ChatMessage, GameHighlight

app = Flask(__name__)
app.config.from_object(Config)

logging.basicConfig(level=logging.INFO)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

online_users = set()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        app.logger.info(f"Registration attempt for user: {username}")

        user = User.query.filter_by(username=username).first()
        if user:
            app.logger.warning(f"Username {username} already exists")
            flash('Username already exists')
            return redirect(url_for('register'))

        user = User.query.filter_by(email=email).first()
        if user:
            app.logger.warning(f"Email {email} already exists")
            flash('Email already exists')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        app.logger.info(f"User {username} registered successfully")
        flash('Registration successful')
        
        login_user(new_user)
        app.logger.info(f"User {username} logged in after registration")
        
        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('index')
        
        app.logger.info(f"Redirecting user {username} to {next_page}")
        return redirect(next_page)

    return render_template('register.html')

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@app.route("/login", methods=['GET', 'POST'])
def login():
    app.logger.info("Login route accessed")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        app.logger.info(f"Login attempt for user: {username}")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            app.logger.info(f"User {username} authenticated successfully")
            login_user(user, remember=True)
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=7)
            app.logger.info(f"User {username} logged in, current_user.is_authenticated: {current_user.is_authenticated}")
            next_page = request.args.get('next')
            app.logger.info(f"Next page after login: {next_page}")
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('index')
            app.logger.info(f"Redirecting to: {next_page}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True, redirect=next_page)
            return redirect(next_page)
        else:
            app.logger.warning(f"Failed login attempt for user: {username}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, message='Invalid username or password')
            flash('Invalid username or password')

    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    app.logger.info(f"User {current_user.username} logged out")
    online_users.discard(current_user.username)
    logout_user()
    return redirect(url_for('index'))

@app.route("/profile")
@login_required
def profile():
    try:
        app.logger.info(f"Accessing profile for user: {current_user.username}")
        high_scores = HighScore.query.filter_by(user_id=current_user.id).order_by(HighScore.score.desc()).first()
        
        user_stats = {}
        for difficulty in ['easy', 'medium', 'hard']:
            stats = db.session.query(func.max(HighScore.score).label('highest_score')).filter_by(
                user_id=current_user.id, difficulty=difficulty).first()
            user_stats[difficulty] = stats.highest_score if stats and stats.highest_score else 0

        app.logger.info(f"Profile data fetched successfully for user: {current_user.username}")
        return render_template('profile.html',
                               user=current_user,
                               highest_score=high_scores.score if high_scores else 0,
                               user_stats=user_stats)
    except Exception as e:
        app.logger.error(f"Error fetching profile data for user {current_user.username}: {str(e)}")
        flash('An error occurred while loading your profile. Please try again later.')
        return redirect(url_for('index'))

@app.route("/submit_score", methods=['POST'])
@login_required
def submit_score():
    data = request.json
    app.logger.info(f"Received score submission: {data}")

    if not data or 'score' not in data or 'difficulty' not in data:
        app.logger.error("Missing score or difficulty in request data")
        return jsonify({'error': 'Score and difficulty are required'}), 400

    if not isinstance(data['score'], int) or not isinstance(data['difficulty'], str):
        app.logger.error("Invalid data types for score or difficulty")
        return jsonify({'error': 'Invalid data types'}), 400

    if data['difficulty'] not in ['easy', 'medium', 'hard']:
        app.logger.error("Invalid difficulty level")
        return jsonify({'error': 'Invalid difficulty level'}), 400

    try:
        new_score = HighScore(user_id=current_user.id,
                              score=data['score'],
                              difficulty=data['difficulty'])
        db.session.add(new_score)
        db.session.commit()

        app.logger.info(f"Score submitted successfully: {new_score.score}")
        
        highlight = f"{current_user.username} scored {data['score']} points in {data['difficulty']} mode!"
        new_highlight = GameHighlight(user_id=current_user.id, highlight=highlight)
        db.session.add(new_highlight)
        db.session.commit()

        return jsonify({'message': 'Score submitted successfully'}), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error submitting score: {str(e)}")
        return jsonify({'error': 'Failed to submit score'}), 500

@app.route("/leaderboard")
def leaderboard():
    return render_template('leaderboard.html')

@app.route("/leaderboard/<difficulty>")
def get_leaderboard(difficulty):
    app.logger.info(f"Fetching leaderboard for difficulty: {difficulty}")
    try:
        scores = HighScore.query.filter_by(difficulty=difficulty).order_by(
            HighScore.score.desc()).limit(10).all()
        leaderboard = [{'username': score.user.username, 'score': score.score, 'date': score.date.strftime('%Y-%m-%d %H:%M:%S')} for score in scores]
        app.logger.info(f"Leaderboard fetched successfully: {leaderboard}")
        return jsonify(leaderboard)
    except Exception as e:
        app.logger.error(f"Error fetching leaderboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch leaderboard'}), 500

@app.route("/forum")
@login_required
def forum():
    app.logger.info(f"User {current_user.username} accessed the forum")
    online_users.add(current_user.username)
    return render_template('forum.html')

@app.route("/send_message", methods=['POST'])
@login_required
def send_message():
    message = request.form.get('message')
    app.logger.info(f"Received message from {current_user.username}: {message}")
    if message:
        new_message = ChatMessage(user_id=current_user.id, message=message)
        db.session.add(new_message)
        db.session.commit()
        app.logger.info(f"Message saved to database: {new_message.id}")
        return jsonify({'status': 'success', 'message': {'id': new_message.id, 'username': current_user.username, 'message': message, 'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}}), 200
    app.logger.warning(f"Empty message received from {current_user.username}")
    return jsonify({'status': 'error', 'message': 'Empty message'}), 400

@app.route("/get_messages")
def get_messages():
    def generate():
        last_id = 0
        last_highlight_id = 0
        while True:
            messages = ChatMessage.query.filter(ChatMessage.id > last_id).order_by(ChatMessage.timestamp.asc()).all()
            highlights = GameHighlight.query.filter(GameHighlight.id > last_highlight_id).order_by(GameHighlight.timestamp.asc()).all()
            
            if messages:
                last_id = messages[-1].id
                message_data = [{'type': 'chat', 'message': {'id': msg.id, 'username': msg.user.username, 'message': msg.message, 'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}} for msg in messages]
                yield f"data: {json.dumps(message_data)}\n\n"
            
            if highlights:
                last_highlight_id = highlights[-1].id
                highlight_data = [{'type': 'highlight', 'highlight': hl.highlight} for hl in highlights]
                yield f"data: {json.dumps(highlight_data)}\n\n"
            
            users_data = {'type': 'users', 'users': list(online_users)}
            yield f"data: {json.dumps([users_data])}\n\n"
            
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream')

@app.context_processor
def inject_user():
    return dict(user=current_user)

@app.cli.command("init_db")
def init_db():
    db.create_all()
    print("Database initialized.")

@app.before_request
def update_last_seen():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)