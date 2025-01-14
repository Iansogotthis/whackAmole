
from flask import Flask, render_template
from app import create_app, db

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    return render_template('index.html')

@app.route('/leaderboard/<difficulty>')
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

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
