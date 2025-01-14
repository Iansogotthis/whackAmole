import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import create_app, db, User, ForumPost, HighScore, ChatMessage
from flask_login import LoginManager

app = create_app()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/game')
@login_required
def game():
    return render_template('index.html')

@app.route('/submit_score', methods=['POST'])
@login_required
def submit_score():
    try:
        if not request.is_json:
            return jsonify({"error": "Content type must be application/json"}), 400
        data = request.get_json()
        if not data or 'score' not in data or 'difficulty' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        score = HighScore(
            user_id=current_user.id,
            score=data['score'],
            difficulty=data['difficulty']
        )
        db.session.add(score)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Error submitting score: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/leaderboard/<difficulty>')
@login_required
def get_leaderboard(difficulty):
    try:
        scores = HighScore.query.filter_by(difficulty=difficulty)\
            .order_by(HighScore.score.desc())\
            .limit(10)\
            .all()
        if request.headers.get('Accept') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "scores": [score.to_dict() for score in scores]
            })
        return render_template('leaderboard.html', leaderboard_scores=scores, current_difficulty=difficulty)
    except Exception as e:
        app.logger.error(f"Error accessing leaderboard: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route("/forum")
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
        return redirect(url_for('forum'))
    except Exception as e:
        app.logger.error(f"Error creating forum post: {str(e)}")
        return redirect(url_for('forum'))

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

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html", selected_friend=None, messages=[])

@app.route("/send_message_any", methods=['POST'])
@login_required
def send_message_any():
    content = request.form.get('content')
    if content:
        message = ChatMessage(
            sender_id=current_user.id,
            receiver_id=current_user.id,  # Placeholder - you may want to specify a receiver
            content=content
        )
        db.session.add(message)
        db.session.commit()
    return redirect(url_for('chat'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            username = request.form['username'].strip()
            email = request.form['email'].strip()
            password = request.form['password']

            # Username validation
            if len(username) < 3:
                flash('Username must be at least 3 characters long')
                return redirect(url_for('register'))

            if len(username) > 20:
                flash('Username must be less than 20 characters')
                return redirect(url_for('register'))

            if not username.isalnum():
                flash('Username must contain only letters and numbers')
                return redirect(url_for('register'))

            # Password validation
            if len(password) < 6:
                flash('Password must be at least 6 characters long')
                return redirect(url_for('register'))

            if len(password) > 50:
                flash('Password is too long')
                return redirect(url_for('register'))

            # Email validation 
            if not '@' in email or not '.' in email:
                flash('Please enter a valid email address')
                return redirect(url_for('register'))

            # Check if username exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return redirect(url_for('register'))

            # Check if email exists
            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return redirect(url_for('register'))

            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.')
            return redirect(url_for('register'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)