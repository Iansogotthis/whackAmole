# Whack-a-Mole Game

A web-based Whack-a-Mole game using Flask and JavaScript with HTML5 Canvas.

## Prerequisites

- Python 3.7 or higher
- PostgreSQL database

## Local Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/whack-a-mole.git
   cd whack-a-mole
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root directory with the following content:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/whack_a_mole
   SECRET_KEY=your_secret_key_here
   ```
   Replace `username`, `password`, and `whack_a_mole` with your PostgreSQL credentials and database name.

5. Initialize the database:
   ```
   python
   >>> from main import db
   >>> db.create_all()
   >>> exit()
   ```

## Running the Application

1. Start the Flask development server:
   ```
   python main.py
   ```

2. Open a web browser and navigate to `http://localhost:5000` to play the game.

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
