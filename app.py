import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
from config import Config
# Configure logging
logging.basicConfig(level=logging.INFO)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Initialize database tables
    with app.app_context():
        try:
            db.create_all()  # Create tables if they don't exist
            db.session.commit()
            migrate.init_app(app, db)  # Initialize migrations
            app.logger.info("Database tables initialized successfully")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error initializing database tables: {str(e)}")

    return app

app = create_app()

# User-Friends Association Table
friends = db.Table('friends',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# Achievement Model
class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(50), nullable=False)  # Icon filename or class
    requirement = db.Column(db.Integer, default=1)  # e.g., score needed or games played

# User Achievement Association Table
user_achievements = db.Table('user_achievements',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('achievement_id', db.Integer, db.ForeignKey('achievement.id'), primary_key=True),
    db.Column('earned_at', db.DateTime, default=datetime.utcnow)
)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_bio = db.Column(db.String(500))
    total_score = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)

    # Relationships
    high_scores = db.relationship('HighScore', backref='player', lazy='dynamic')
    forum_posts = db.relationship('ForumPost', backref='author_user', lazy='dynamic')
    achievements = db.relationship('Achievement', secondary=user_achievements, lazy='subquery',
                                 backref=db.backref('users', lazy=True))
    friends_list = db.relationship('User', secondary=friends,
                                 primaryjoin=(friends.c.user_id == id),
                                 secondaryjoin=(friends.c.friend_id == id),
                                 backref=db.backref('friend_of', lazy='dynamic'),
                                 lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_friend(self, user):
        if user not in self.friends_list:
            self.friends_list.append(user)
            user.friends_list.append(self)

    def remove_friend(self, user):
        if user in self.friends_list:
            self.friends_list.remove(user)
            user.friends_list.remove(self)

    def get_achievements(self):
        return Achievement.query.join(
            user_achievements
        ).filter(user_achievements.c.user_id == self.id).all()

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

# High Score model
class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'player_name': self.player.username,
            'score': self.score,
            'difficulty': self.difficulty,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S')
        }

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@app.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/submit_score", methods=['POST'])
@login_required
def submit_score():
    data = request.json
    app.logger.info(f"Received score submission: {data}")
    try:
        new_score = HighScore(
            user_id=current_user.id if current_user.is_authenticated else None,
            score=data['score'],
            difficulty=data['difficulty']
        )
        db.session.add(new_score)
        db.session.commit()
        app.logger.info(f"Score submitted successfully: {new_score.to_dict()}")
        return jsonify({'message': 'Score submitted successfully'}), 201
    except Exception as e:
        app.logger.error(f"Error submitting score: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit score'}), 500

@app.route("/leaderboard/<difficulty>")
def get_leaderboard(difficulty):
    app.logger.info(f"Fetching leaderboard for difficulty: {difficulty}")
    if not current_user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    try:
        scores = HighScore.query.filter_by(difficulty=difficulty).order_by(HighScore.score.desc()).limit(10).all()
        leaderboard = []
        for score in scores:
            score_data = {
                'rank': len(leaderboard) + 1,
                'player_name': score.player.username if score.player else 'Anonymous',
                'score': score.score,
                'date': score.date.strftime('%Y-%m-%d %H:%M')
            }
            leaderboard.append(score_data)
        app.logger.info(f"Leaderboard fetched successfully: {leaderboard}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'scores': leaderboard})
        return render_template('index.html', leaderboard_scores=leaderboard, current_difficulty=difficulty)
    except Exception as e:
        app.logger.error(f"Error fetching leaderboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch leaderboard', 'scores': []}), 500

@app.route("/forum")
@login_required
def forum():
    try:
        posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
        top_scores = HighScore.query.order_by(HighScore.score.desc()).limit(5).all()
        return render_template("forum.html", posts=posts, top_scores=top_scores)
    except Exception as e:
        app.logger.error(f"Error accessing forum: {str(e)}")
        return render_template("forum.html", posts=[], top_scores=[])

@app.route("/create_post", methods=['POST'])
@login_required
def create_post():
    try:
        new_post = ForumPost(
            title=request.form['title'],
            content=request.form['content'],
            author_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        app.logger.info(f"New forum post created: {new_post.title}")
        return redirect(url_for('forum'))
    except Exception as e:
        app.logger.error(f"Error creating forum post: {str(e)}")
        return redirect(url_for('forum'))

@app.route("/profile/<username>")
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    messages = []
    if user != current_user:
        messages = ChatMessage.query.filter(
            ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == user.id)) |
            ((ChatMessage.sender_id == user.id) & (ChatMessage.receiver_id == current_user.id))
        ).order_by(ChatMessage.sent_at.asc()).all()
    return render_template("profile.html", user=user, messages=messages, HighScore=HighScore)

@app.route("/add_friend/<username>", methods=['POST'])
@login_required
def add_friend(username):
    friend = User.query.filter_by(username=username).first_or_404()
    if friend != current_user:
        current_user.add_friend(friend)
        db.session.commit()
        flash(f'You are now friends with {username}!')
    return redirect(url_for('profile', username=username))

@app.route("/remove_friend/<username>", methods=['POST'])
@login_required
def remove_friend(username):
    friend = User.query.filter_by(username=username).first_or_404()
    if friend != current_user:
        current_user.remove_friend(friend)
        db.session.commit()
        flash(f'You are no longer friends with {username}.')
    return redirect(url_for('profile', username=username))

@app.route("/chat")
@app.route("/chat/<int:friend_id>")
@login_required
def chat(friend_id=None):
    if friend_id:
        friend = User.query.get_or_404(friend_id)
        if friend not in current_user.friends_list:
            flash('You can only chat with your friends.')
            return redirect(url_for('chat'))

        # Mark messages as read
        unread_messages = ChatMessage.query.filter_by(
            sender_id=friend.id,
            receiver_id=current_user.id,
            read=False
        ).all()
        for message in unread_messages:
            message.read = True
        db.session.commit()

        # Get chat history
        messages = ChatMessage.query.filter(
            ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == friend.id)) |
            ((ChatMessage.sender_id == friend.id) & (ChatMessage.receiver_id == current_user.id))
        ).order_by(ChatMessage.sent_at.asc()).all()

        return render_template("chat.html", selected_friend=friend, messages=messages)
    return render_template("chat.html", selected_friend=None, messages=[])

@app.route("/send_message/<int:friend_id>", methods=['POST'])
@login_required
def send_message(friend_id):
    try:
        friend = User.query.get_or_404(friend_id)
        if friend not in current_user.friends_list:
            flash('You can only send messages to your friends.')
            return redirect(url_for('chat'))

        content = request.form.get('content', '').strip()
        if not content:
            flash('Message cannot be empty.')
            return redirect(url_for('chat', friend_id=friend_id))

        message = ChatMessage(
            sender_id=current_user.id,
            receiver_id=friend_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error sending message: {str(e)}")
        flash('Failed to send message. Please try again.')

    return redirect(url_for('chat', friend_id=friend_id))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))

        flash('Invalid username or password')

    return render_template('login.html')

@app.route("/search_users", methods=['GET'])
@login_required
def search_users():
    query = request.args.get('query', '')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if query:
            try:
                users = User.query.filter(User.username.ilike(f'%{query}%')).all()
                results = [{
                    'username': user.username,
                    'id': user.id,
                    'games_played': user.games_played,
                    'is_friend': user in current_user.friends_list
                } for user in users if user != current_user]
                return jsonify(results)
            except Exception as e:
                app.logger.error(f"Search error: {str(e)}")
                return jsonify({'error': 'Search failed'}), 500
        return jsonify([])
    return render_template('search.html')

@app.route("/send_emoji", methods=['POST'])
@login_required
def send_emoji():
    data = request.json
    recipient = User.query.get_or_404(data['recipient_id'])
    emoji = data['emoji']
    message = ChatMessage(
        sender_id=current_user.id,
        receiver_id=recipient.id,
        content=f"Sent {emoji}"
    )
    db.session.add(message)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login')) # Redirect to login after logout

if __name__ == "__main__":
    if app.config['SQLALCHEMY_DATABASE_URI'] is None:
        app.logger.error("Database URI is not configured. Please set DATABASE_URL environment variable.")
    else:
        try:
            with app.app_context():
                db.create_all()
                app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")

    app.run(host="0.0.0.0", port=80, debug=False)