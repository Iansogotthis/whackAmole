import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from whackamole.app import app, db, User, ForumPost, HighScore, ChatMessage
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/game')
@login_required
def game():
    return render_template('index.html')






@app.route("/send_friend_request/<int:user_id>", methods=['POST'])
@login_required
def send_friend_request(user_id):
    user = User.query.get_or_404(user_id)
    current_user.add_friend(user)
    db.session.commit()
    flash(f'Friend request sent to {user.username}!')
    return redirect(url_for('search_users'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080, debug=True)