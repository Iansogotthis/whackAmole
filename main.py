import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config
from sqlalchemy import func, text
import json
import time

app = Flask(__name__)
app.config.from_object(Config)

logging.basicConfig(level=logging.INFO)

try:
    db = SQLAlchemy(app)
    with app.app_context():
        db.create_all()
except Exception as e:
    app.logger.error(f"Database connection error: {str(e)}")
    print(f"Error connecting to the database: {str(e)}")

login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, score, difficulty):
        self.user_id = user_id
        self.score = score
        self.difficulty = difficulty

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.user.username,
            'score': self.score,
            'difficulty': self.difficulty,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S')
        }


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('messages', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.user.username,
            'message': self.message,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }


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

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful')
        login_user(new_user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))

    return render_template('register.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
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

        app.logger.info(f"Score submitted successfully: {new_score.to_dict()}")
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
            HighScore.score.desc()).limit(5).all()
        leaderboard = [score.to_dict() for score in scores]
        app.logger.info(f"Leaderboard fetched successfully: {leaderboard}")
        return jsonify(leaderboard)
    except Exception as e:
        app.logger.error(f"Error fetching leaderboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch leaderboard'}), 500


@app.route("/forum")
@login_required
def forum():
    app.logger.info(f"User {current_user.username} accessed the forum")
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
        app.logger.info(f"Message saved to database: {new_message.to_dict()}")
        return jsonify({'status': 'success'}), 200
    app.logger.warning(f"Empty message received from {current_user.username}")
    return jsonify({'status': 'error', 'message': 'Empty message'}), 400


@app.route("/get_messages")
def get_messages():
    def generate():
        last_id = 0
        while True:
            messages = ChatMessage.query.filter(ChatMessage.id > last_id).order_by(ChatMessage.timestamp.asc()).all()
            if messages:
                last_id = messages[-1].id
                message_data = [msg.to_dict() for msg in messages]
                app.logger.info(f"Sending messages: {message_data}")
                yield f"data: {json.dumps(message_data)}\n\n"
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream')


@app.context_processor
def inject_user():
    return dict(user=current_user)


def init_db():
    with app.app_context():
        db.create_all()
        db.session.execute(
            text(
                'ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255);'
            ))
        db.session.commit()


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)