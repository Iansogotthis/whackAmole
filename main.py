import logging
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import Config
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)