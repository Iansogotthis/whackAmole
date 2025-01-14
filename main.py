from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import create_app, db, User, ForumPost, HighScore
from flask_login import LoginManager

app = create_app()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
@login_required
def game():
    return render_template('index.html')

@app.route('/leaderboard/<difficulty>')
@login_required
def get_leaderboard(difficulty):
    try:
        scores = HighScore.query.filter_by(difficulty=difficulty)\
            .order_by(HighScore.score.desc())\
            .limit(10)\
            .all()
        return render_template('index.html', leaderboard_scores=scores, current_difficulty=difficulty)
    except Exception as e:
        app.logger.error(f"Error accessing leaderboard: {str(e)}")
        return render_template('index.html', leaderboard_scores=[], current_difficulty=difficulty)

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

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database initialization error: {e}")

    app.run(host='0.0.0.0', port=3000, debug=True)