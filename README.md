# Whack-a-Mole Game

A web-based Whack-a-Mole game using Flask and JavaScript with HTML5 Canvas.

## Prerequisites

- Python 3.7 or higher
- PostgreSQL database (provided by Replit)

## Build and Deployment Steps

1. Install Dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize Database:
```bash
python -c "from main import app, db; app.app_context().push(); db.create_all()"
```

3. Run Migrations:
```bash
flask db upgrade
```

4. Run Application:
```bash
python main.py
```

The application will be available on port 8080.


## Running on Replit

1. Click the "Run" button at the top of the Replit interface.
2. The server will start automatically on port 8080.
3. Access the game through the webview or open in a new tab.

## Deployment on Replit

1. Click the "Deploy" button in the toolbar
2. Select "Deploy to Production"
3. Wait for the deployment process to complete
4. Access your deployed game using the provided URL


## Game Instructions

- Select a difficulty level (Easy, Medium, or Hard) and click "Start Game".
- Click on the moles as they appear to whack them and earn points.
- Different types of moles give different points:
  - Normal Mole: 1 point
  - Fast Mole (Red): 2 points
  - Golden Mole: 5 points
- Collect power-ups to gain advantages:
  - Hammer (Red): Increases mole point value by 1 for 3 seconds
  - Freeze (Blue): Slows down mole disappearance for 3 seconds
- Try to reach the target score before time runs out:
  - Easy: 30 points
  - Medium: 50 points
  - Hard: 80 points

Enjoy playing Whack-a-Mole!