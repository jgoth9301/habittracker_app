import sqlite3
from datetime import date


def get_db(name="main.db"):
    """
    Connects to the specified SQLite database, initializes necessary tables, and returns the database connection.

    Args:
        name (str): The name of the database file. Defaults to "main.db".

    Returns:
        sqlite3.Connection: The database connection object.
    """
    db = sqlite3.connect(name)
    create_table(db)
    return db

def create_table(db):
    """
    Creates necessary tables in the database and populates them with default data if they do not already exist.

    This function sets up the database schema by creating the 'counter', 'tracker',
    and 'predefinedHabits' tables. It also populates the 'counter' and
    'predefinedHabits' tables with default values if they are empty.

    Args:
        db: The database connection object.

    Returns:
        None
    """

    cur = db.cursor()

    # Create the 'counter' table if it does not already exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS counter (
            name TEXT PRIMARY KEY,
            description TEXT,
            interval TEXT,
            period INTEGER,
            creation DATE
        )
    """)

    # Load of historic master data for predefined habits
    cur.executemany("""
        INSERT OR IGNORE INTO counter (name, description, interval, period, creation) 
        VALUES (?, ?, ?, ?, ?)
    """, [
        ('Meditation', '10 minutes of daily meditation for improved mental well-being', 'daily', '31', '2021-12-01'),
        ('Reading', 'Read a book for 20 minutes each day', 'daily', '31', '2021-12-01'),
        ('Exercise', 'Exercise for 30 minutes every day', 'daily', '31', '2021-12-01'),
        ('Cleaning', 'Completely clean your house every month', 'monthly', '12', '2021-01-01'),
    ])

    # Create the 'tracker' table if it does not already exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tracker (
            date DATE NOT NULL,
            counterName TEXT NOT NULL,
            FOREIGN KEY (counterName) REFERENCES counter(name)
        )
    """)

    # Create the 'predefinedHabits' table if it does not already exist"
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predefinedHabits (
            name TEXT PRIMARY KEY,
            description TEXT,
            interval TEXT
        )
    """)

    # Definition of predefined habits for initial load
    prehabits = [
        ('Meditation', '10 minutes of daily meditation for improved mental well-being', 'daily'),
        ('Reading', 'Read a book for 20 minutes each day', 'daily'),
        ('Exercise', 'Exercise for 30 minutes every day', 'daily'),
        ('Cleaning', 'Completely clean your house every month', 'monthly'),
        ('Holiday', 'Plan a minimum four-weeks holiday once a year', 'yearly')
    ]

    # Check if the "predefinedHabits" table already has data
    cur.execute("SELECT COUNT(*) FROM predefinedHabits")
    if cur.fetchone()[0] == 0:  # If table is empty, insert initial habits
        # Insert the values into the "predefinedHabits" table
        cur.executemany("INSERT INTO predefinedHabits (name, description, interval) VALUES (?, ?, ?)", prehabits)

    db.commit()


def add_counter(db, name, description, interval, period, creation):
    """
    Adds a new counter to the 'counter' table in the database.

    Inserts a new row with the specified name, description, interval, and creation timestamp.

    Args:
        db: The database connection object.
        name (str): The name of the counter.
        description (str): A description of the counter.
        interval (str): The interval type (e.g., "daily", "weekly").
        creation (str): The creation timestamp in ISO format (YYYY-MM-DD).

    Returns:
        None

    Side Effects:
        - Inserts a row into the 'counter' table.
        - Commits the transaction.
        - Prints a success or error message.
    """
    try:
        cur = db.cursor()
        cur.execute("""
            INSERT INTO counter (name, description, interval, period, creation)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, interval, period, creation))
        db.commit()
        print(f"Counter '{name}' added successfully.")
    except Exception as e:
        print(f"Error adding counter '{name}': {e}")
    finally:
        cur.close()

def increment_counter(db, name, event_date=None):
    """
    Increments a counter by adding a new entry to the 'tracker' table.

    This function inserts a new row into the 'tracker' table with the specified
    counter name and an event date. If no event date is provided, the current
    date (in ISO format) is used by default.

    Args:
        db: The database connection object, which provides access to the database.
        name (str): The name of the counter to increment.
        event_date (str, optional): The date associated with the increment.
        If not provided, the current date in ISO format (YYYY-MM-DD) is used.

    Returns:
        None

    Raises:
        Exception: Any exceptions during database operations are propagated to the caller.

    Side Effects:
        - Inserts a new row into the 'tracker' table.
        - Commits the transaction to the database.
    """
    cur = db.cursor()
    if not event_date:
        event_date = date.today().isoformat()  # Use ISO format for consistency
    cur.execute("INSERT INTO tracker (date, counterName) VALUES (?, ?)", (event_date, name))
    db.commit()


def get_counter_data(db, name):
    """
    Fetches all data from the 'tracker' table for a specific counter name.

    This function retrieves rows from the 'tracker' table in the database
    where the 'counterName' matches the specified name. It uses a parameterized
    query to prevent SQL injection.

    Args:
        db: The database connection object, which provides access to the database.
        name (str): The name of the counter to filter rows by.

    Returns:
        list of tuple: A list of rows (as tuples) that match the specified counter name.
        Each tuple represents a row in the table. If no matching rows are found,
        an empty list is returned.

    Raises:
         Exception: Any exceptions during database operations are propagated to the caller.
    """
    cur = db.cursor()
    cur.execute("SELECT * FROM tracker WHERE counterName = ?", (name,))
    return cur.fetchall()


def get_predefined_habits(db):
    """
    Fetches all predefined habits with concatenated details from the database.

    Queries the 'predefinedHabits' table to retrieve habits in the format
    "name - description (interval)".

    Args:
        db: The database connection object.

    Returns:
        list of str: A list of concatenated habit details, or an empty list
        if an error occurs.
    """
    try:
        # Query to concatenate the name, description, and interval
        habits = db.execute("""
            SELECT name || ' - ' || description || ' (' || interval || ')' AS habit_details
            FROM predefinedHabits
        """).fetchall()

        # Extract the concatenated habit details as a list of strings
        return [habit[0] for habit in habits]
    except Exception as e:
        print(f"Error fetching predefined habits: {e}")
        return []


def get_habit_dates(db, habit_name):
    """
    Fetch all dates associated with a given habit name from the database.

    Args:
        db: Database connection object.
        habit_name (str): The name of the habit to fetch dates for.

    Returns:
        list: A list of dates (strings) associated with the habit.
    """
    try:
        # Query to retrieve all dates for the given habit name
        dates = db.execute(
            "SELECT date FROM tracker WHERE Name = ? ORDER BY date ASC", (habit_name,)
        ).fetchall()

        # Extract dates from the query result
        return [date[0] for date in dates]
    except Exception as e:
        print(f"Error fetching dates for habit '{habit_name}': {e}")
        return []

def get_existing_habits(db):
    """
    Retrieves concatenated habit details from the 'counter' table.

    Args:
        db: The database connection object.

    Returns:
        list of str: A list of habit details in the format "name - description (interval)",
        or an empty list if no habits exist or an error occurs.
    """
    try:
        # Query to concatenate the name, description, and interval
        habits = db.execute("""
            SELECT name || ' - ' || description || ' (' || interval || ')' AS habit_details
            FROM counter
        """).fetchall()

        # If no habits exist, return an empty list
        if not habits:
            print("No habits found in the database.")
            return []

        # Extract the concatenated habit details as a list of strings
        return [habit[0] for habit in habits]

    except Exception as e:
        print(f"Error fetching existing habits: {e}")
        return []

def get_existing_habits_short(db):
    """
    Retrieves habit names from the 'counter' table.

    Args:
        db: The database connection object.

    Returns:
        list of str: A list of habit names, or an empty list if no habits exist or an error occurs.
    """
    try:
        # Query to fetch habit names
        habits = db.execute("""
            SELECT name
            FROM counter
        """).fetchall()

        # Check if any habits exist
        if not habits:
            print("No habits found in the database.")
            return []

        # Extract habit names as a list of strings
        return [habit[0] for habit in habits]

    except sqlite3.Error as e:
        print(f"Database error while fetching habits: {e}")
        return []

def initial_load_tracker(cur):
    """
    Initializes the tracker by inserting predefined data only if it does not already exist.

    Args:
        cur: Cursor object of the database connection.

    Returns:
        int: Number of newly inserted rows.
    """
    # Example data for the initial load
    tracking_data = [
        ('2021-12-01', 'Meditation'),
        ('2021-12-02', 'Meditation'),
        ('2021-12-03', 'Meditation'),
        ('2021-12-04', 'Meditation'),
        ('2021-12-05', 'Meditation'),
        ('2021-12-06', 'Meditation'),
        ('2021-12-07', 'Meditation'),
        ('2021-12-08', 'Meditation'),

        ('2021-12-10', 'Meditation'),
        ('2021-12-11', 'Meditation'),
        ('2021-12-12', 'Meditation'),
        ('2021-12-13', 'Meditation'),
        ('2021-12-14', 'Meditation'),
        ('2021-12-15', 'Meditation'),
        ('2021-12-16', 'Meditation'),
        ('2021-12-17', 'Meditation'),
        ('2021-12-18', 'Meditation'),

        ('2021-12-20', 'Meditation'),
        ('2021-12-21', 'Meditation'),
        ('2021-12-22', 'Meditation'),
        ('2021-12-23', 'Meditation'),
        ('2021-12-24', 'Meditation'),
        ('2021-12-25', 'Meditation'),
        ('2021-12-26', 'Meditation'),
        ('2021-12-27', 'Meditation'),
        ('2021-12-28', 'Meditation'),
        ('2021-12-29', 'Meditation'),
        ('2021-12-30', 'Meditation'),
        ('2021-12-31', 'Meditation'),

        ('2021-12-01', 'Reading'),
        ('2021-12-02', 'Reading'),
        ('2021-12-03', 'Reading'),
        ('2021-12-04', 'Reading'),
        ('2021-12-05', 'Reading'),
        ('2021-12-06', 'Reading'),

        ('2021-12-12', 'Reading'),
        ('2021-12-13', 'Reading'),
        ('2021-12-14', 'Reading'),
        ('2021-12-15', 'Reading'),
        ('2021-12-16', 'Reading'),
        ('2021-12-17', 'Reading'),
        ('2021-12-18', 'Reading'),
        ('2021-12-20', 'Reading'),
        ('2021-12-21', 'Reading'),
        ('2021-12-22', 'Reading'),
        ('2021-12-23', 'Reading'),
        ('2021-12-24', 'Reading'),
        ('2021-12-25', 'Reading'),
        ('2021-12-26', 'Reading'),
        ('2021-12-27', 'Reading'),
        ('2021-12-28', 'Reading'),
        ('2021-12-29', 'Reading'),
        ('2021-12-30', 'Reading'),
        ('2021-12-31', 'Reading'),

        ('2021-12-01', 'Exercise'),
        ('2021-12-02', 'Exercise'),
        ('2021-12-03', 'Exercise'),
        ('2021-12-04', 'Exercise'),
        ('2021-12-05', 'Exercise'),
        ('2021-12-06', 'Exercise'),
        ('2021-12-07', 'Exercise'),
        ('2021-12-08', 'Exercise'),
        ('2021-12-09', 'Exercise'),
        ('2021-12-10', 'Exercise'),
        ('2021-12-11', 'Exercise'),
        ('2021-12-12', 'Exercise'),
        ('2021-12-13', 'Exercise'),
        ('2021-12-14', 'Exercise'),
        ('2021-12-15', 'Exercise'),
        ('2021-12-16', 'Exercise'),
        ('2021-12-17', 'Exercise'),
        ('2021-12-18', 'Exercise'),
        ('2021-12-19', 'Exercise'),
        ('2021-12-20', 'Exercise'),
        ('2021-12-21', 'Exercise'),
        ('2021-12-22', 'Exercise'),
        ('2021-12-23', 'Exercise'),
        ('2021-12-24', 'Exercise'),
        ('2021-12-25', 'Exercise'),
        ('2021-12-26', 'Exercise'),
        ('2021-12-27', 'Exercise'),
        ('2021-12-28', 'Exercise'),
        ('2021-12-29', 'Exercise'),
        ('2021-12-30', 'Exercise'),
        ('2021-12-31', 'Exercise'),

        ('2021-01-01', 'Cleaning'),
        ('2021-02-02', 'Cleaning'),
        ('2021-03-03', 'Cleaning'),
        ('2021-04-04', 'Cleaning'),
        ('2021-05-05', 'Cleaning'),
        ('2021-06-06', 'Cleaning'),
        ('2021-07-07', 'Cleaning'),
        ('2021-08-08', 'Cleaning'),
        ('2021-09-08', 'Cleaning'),
        ('2021-10-08', 'Cleaning'),
        ('2021-11-08', 'Cleaning'),
        ('2021-12-09', 'Cleaning')
    ]

    # Step 1: Retrieve existing data
    existing_data_query = """
        SELECT date, counterName FROM tracker
    """
    cur.execute(existing_data_query)
    existing_data = set(cur.fetchall())

    # Step 2: Filter new data
    new_data = [entry for entry in tracking_data if entry not in existing_data]

    # Step 3: Insert new data
    if new_data:
        cur.executemany("""
            INSERT INTO tracker (date, counterName) 
            VALUES (?, ?)
        """, new_data)
        print(f"Inserted {len(new_data)} new rows into tracker.")
    else:
        print("No new data to insert. All values already exist.")

    # Return the number of inserted rows
    return len(new_data)