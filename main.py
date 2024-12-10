import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.INFO)

db = SQLAlchemy(app)

# High Score model
class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'player_name': self.player_name,
            'score': self.score,
            'difficulty': self.difficulty,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S')
        }

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit_score", methods=['POST'])
def submit_score():
    data = request.json
    app.logger.info(f"Received score submission: {data}")
    try:
        new_score = HighScore(
            player_name=data['player_name'],
            score=data['score'],
            difficulty=data['difficulty']
        )
        db.session.add(new_score)
        db.session.commit()
        app.logger.info(f"Score submitted successfully: {new_score.to_dict()}")
        return jsonify({'message': 'Score submitted successfully'}), 201
    except Exception as e:
        app.logger.error(f"Error submitting score: {str(e)}")
        return jsonify({'error': 'Failed to submit score'}), 500

@app.route("/leaderboard/<difficulty>")
def get_leaderboard(difficulty):
    app.logger.info(f"Fetching leaderboard for difficulty: {difficulty}")
    try:
        scores = HighScore.query.filter_by(difficulty=difficulty).order_by(HighScore.score.desc()).limit(10).all()
        leaderboard = [score.to_dict() for score in scores]
        app.logger.info(f"Leaderboard fetched successfully: {leaderboard}")
        return jsonify(leaderboard)
    except Exception as e:
        app.logger.error(f"Error fetching leaderboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch leaderboard'}), 500

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
def create_post():
    try:
        new_post = ForumPost(
            title=request.form['title'],
            content=request.form['content'],
            author="Anonymous"  # For now, we'll use Anonymous as the author
        )
        db.session.add(new_post)
        db.session.commit()
        app.logger.info(f"New forum post created: {new_post.title}")
        return redirect(url_for('forum'))
    except Exception as e:
        app.logger.error(f"Error creating forum post: {str(e)}")
        return redirect(url_for('forum'))

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
    
    app.run(host="0.0.0.0", port=5000, debug=True)
