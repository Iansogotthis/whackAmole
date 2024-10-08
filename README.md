# Whack-a-Mole Game

A web-based Whack-a-Mole game using Flask and JavaScript with HTML5 Canvas, featuring user accounts and saved game stats.

## Prerequisites

- Python 3.7 or higher
- PostgreSQL database
- Cassandra database (optional)

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
   CASSANDRA_KEYSPACE=your_cassandra_keyspace
   CASSANDRA_HOSTS=cassandra_host1,cassandra_host2
   CASSANDRA_BUNDLE=/path/to/cassandra/bundle.pem
   CASSANDRA_USERNAME=cassandra_username
   CASSANDRA_PASSWORD=cassandra_password
   ```
   Replace the values with your actual database credentials and settings.

5. Initialize the database:
   ```
   flask db upgrade
   ```

## Running the Application

1. Start the Flask development server:
   ```
   python main.py
   ```

2. Open a web browser and navigate to `http://localhost:5000` to play the game.

## Game Instructions

(Keep the existing game instructions)

## Features

(Keep the existing features list)

Enjoy playing Whack-a-Mole!
