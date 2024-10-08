import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash
from models import db, User, HighScore, ChatMessage, GameHighlight
from config import Config
import json
import time
from sqlalchemy import desc
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Set up Cassandra connection (if needed)
cassandra_session = None
if app.config['CASSANDRA_KEYSPACE']:
    try:
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider

        auth_provider = PlainTextAuthProvider(
            username=app.config['CASSANDRA_USERNAME'],
            password=app.config['CASSANDRA_PASSWORD']
        )
        
        cluster = Cluster(
            app.config['CASSANDRA_HOSTS'].split(','),
            auth_provider=auth_provider,
            ssl_context=app.config['CASSANDRA_BUNDLE']
        )
        
        cassandra_session = cluster.connect(app.config['CASSANDRA_KEYSPACE'])
        print("Cassandra connection established successfully")
    except Exception as e:
        print(f"Error connecting to Cassandra: {str(e)}")
        print("Continuing without Cassandra support")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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

@app.route("/forum")
@login_required
def forum():
    return render_template('forum.html', user=current_user)

@app.route("/send_message", methods=['POST'])
@login_required
def send_message():
    message = request.form.get('message')
    if message:
        new_message = ChatMessage(user_id=current_user.id, message=message)
        db.session.add(new_message)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': {
                'id': new_message.id,
                'username': current_user.username,
                'message': new_message.message,
                'timestamp': new_message.timestamp.isoformat()
            }
        }), 200
    return jsonify({'status': 'error', 'message': 'Empty message'}), 400

@app.route("/get_messages")
def get_messages():
    def generate():
        last_id = 0
        last_highlight_id = 0
        while True:
            messages = ChatMessage.query.filter(ChatMessage.id > last_id).order_by(ChatMessage.timestamp.asc()).all()
            highlights = GameHighlight.query.filter(GameHighlight.id > last_highlight_id).order_by(GameHighlight.timestamp.asc()).all()
            
            data = []
            if messages:
                last_id = messages[-1].id
                data.extend([{'type': 'chat', 'message': msg.to_dict()} for msg in messages])
            
            if highlights:
                last_highlight_id = highlights[-1].id
                data.extend([{'type': 'highlight', 'highlight': hl.to_dict()} for hl in highlights])
            
            online_users = User.query.filter(User.last_seen >= (datetime.utcnow() - timedelta(minutes=5))).all()
            data.append({'type': 'users', 'users': [user.username for user in online_users]})
            
            if data:
                yield f"data: {json.dumps(data)}\n\n"
            
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream')

@app.route("/get_more_messages")
@login_required
def get_more_messages():
    last_id = int(request.args.get('last_id', 0))
    limit = int(request.args.get('limit', 20))
    messages = ChatMessage.query.filter(ChatMessage.id < last_id).order_by(desc(ChatMessage.timestamp)).limit(limit).all()
    return jsonify({
        'messages': [msg.to_dict() for msg in messages]
    })

@app.route("/leaderboard/<difficulty>")
def leaderboard(difficulty):
    scores = HighScore.query.filter_by(difficulty=difficulty).order_by(HighScore.score.desc()).limit(10).all()
    return jsonify([score.to_dict() for score in scores])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
