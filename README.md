# Whack-a-Mole Game

Welcome to the adrenaline-pumping world of the Whack-a-Mole Game, a sensational web-based experience crafted with the mastery of Flask and brought to life with JavaScript using the dynamic HTML5 Canvas!

## What You’ll Need

- Python 3.7 or newer
- PostgreSQL database (thanks to Replit)

## Ready to Launch?

1. **Grab the Essentials**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set the Stage**:
   ```bash
   python -c "from main import app, db; app.app_context().push(); db.create_all()"
   ```

3. **Level Up with Migrations**:
   ```bash
   flask db upgrade
   ```

4. **Start Your Engines!**:
   ```bash
   python main.py
   ```
   
   Get ready to dive in on **port 8080** – let the mole-whacking madness begin!


## Thriving on Replit

1. Smash that **Run** button in Replit’s toolbar.
2. Watch as the server breathes life on **port 8080**.
3. Dive into the game via webview or open it in a tab to feel the action!

## Deploy on Replit

1. Hit **Deploy** in the toolbar.
2. Opt for **Deploy to Production**.
3. Hold tight as magic unfolds, completing deployment.
4. Claim your piece of mole-whacking glory through the URL!


## Mastering the Game

- Pick your warrior path: Easy, Medium, or Hard, and embark on the challenge by clicking **Start Game**.
- Unleash your reflexes and zap those moles out of their holes to escalate your score.
- Discover strategic mole types:
  - **Normal Mole**: +1 point
  - **Fast Mole (Red)**: +2 points
  - **Golden Mole**: +5 points - the jackpot!
- Snag power-ups for the upper hand:
  - **Hammer (Red)**: Boost point value by 1 for 3 electrifying seconds
  - **Freeze (Blue)**: Slow mole vanish for 3 crucial seconds
- Conquer the game by hitting target scores before the clock ticks out:
  - **Easy**: 30 points
  - **Medium**: 50 points
  - **Hard**: 80 points

Get ready for a whirlwind of fun and excitement with Whack-a-Mole! Let’s whack!  