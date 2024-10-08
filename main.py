from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Score, Message
import random
from flask_sse import sse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config["REDIS_URL"] = "redis://localhost"
db.init_app(app)
app.register_blueprint(sse, url_prefix='/stream')

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return jsonify(success=True)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify(success=True)
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/submit_score', methods=['POST'])
@login_required
def submit_score():
    try:
        data = request.get_json()
        score = data.get('score')
        difficulty = data.get('difficulty')

        if score is None or difficulty is None:
            return jsonify({'error': 'Score or difficulty missing'}), 400

        new_score = Score(user_id=current_user.id, score=score, difficulty=difficulty)
        db.session.add(new_score)
        db.session.commit()
        return jsonify({'message': 'Score submitted successfully'}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in submit_score: {e}")
        return jsonify({'error': 'Failed to submit score'}), 500

@app.route('/get_leaderboard/<difficulty>')
def get_leaderboard(difficulty):
    try:
        scores = Score.query.filter_by(difficulty=difficulty).order_by(Score.score.desc()).limit(10).all()
        leaderboard_data = [score.to_dict() for score in scores]
        return jsonify(leaderboard_data)
    except Exception as e:
        app.logger.error(f"Error in get_leaderboard: {e}")
        return jsonify({'error': 'Failed to fetch leaderboard'}), 500

@app.route('/ai_move', methods=['POST'])
def ai_move():
    return jsonify(x=random.randint(0, 400), y=random.randint(0, 400))

@app.route('/forum')
@login_required
def forum():
    return render_template('forum.html')

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    message = request.form.get('message')
    if message:
        new_message = Message(user_id=current_user.id, content=message)
        db.session.add(new_message)
        db.session.commit()
        sse.publish({"message": message, "username": current_user.username}, type='chat')
        return jsonify(status='success')
    return jsonify(status='error', message='Empty message'), 400

@app.route('/get_messages')
def get_messages():
    messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()
    return jsonify([{
        'username': message.user.username,
        'message': message.content,
        'timestamp': message.timestamp.isoformat()
    } for message in messages])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
