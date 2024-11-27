import matplotlib.pyplot as plt
import sqlite3
from matplotlib.ticker import MaxNLocator
import pandas as pd
from datetime import datetime, timedelta

def total_habit(db):
    """
    Count the number of entries in the 'counter' table.

    Args:
        db: The database connection object.

    Returns:
        int: The number of entries in the 'counter' table.
    """
    try:
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM counter")
        return cur.fetchone()[0]
    except Exception as e:
        print(f"Error calculating total count: {e}")
        return 0

def total_tracker(db):
    """
    Count the number of entries in the 'tracker' table.

    Args:
        db: The database connection object.

    Returns:
        int: The number of entries in the 'tracker' table.
    """
    try:
        cur = db.cursor()  # Cursor erstellen
        cur.execute("SELECT COUNT(*) FROM tracker")
        return cur.fetchone()[0]  # Gibt die Gesamtanzahl der Einträge zurück
    except Exception as e:
        print(f"Error calculating total habits: {e}")
        return 0  # Gibt 0 zurück, falls ein Fehler auftritt


def total_tracker_habit(db, habit_name):
    """
    Count the number of entries in the 'tracker' table for a specific habit.

    Args:
        db: The database connection object.
        habit_name (str): The name of the habit to filter by.

    Returns:
        int: The number of entries in the 'tracker' table for the specified habit.
    """
    cur = None  # Initialisieren des Cursors
    try:
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM tracker WHERE counterName = ?", (habit_name,))
        return cur.fetchone()[0]
    except Exception as e:
        print(f"Error calculating entries for habit '{habit_name}': {e}")
        return 0
    finally:
        if cur:
            cur.close()

def plot_tracker_counts(db, habit_name):
    """
    Fetch tracker counts per date for a given habit, fill missing dates, and plot the results.

    Args:
        db: Database connection object.
        habit_name (str): The name of the habit to analyze.

    Returns:
        None
    """
    try:
        cur = db.cursor()
        cur.execute("""
            SELECT date, COUNT(*) as count
            FROM tracker
            WHERE counterName = ?
            GROUP BY date
            ORDER BY date ASC
        """, (habit_name,))
        data = cur.fetchall()
        cur.close()

        if data:
            # Prepare data as a DataFrame
            df = pd.DataFrame(data, columns=['date', 'count'])
            df['date'] = pd.to_datetime(df['date'])  # Convert to datetime

            # Create a complete date range from the first to the last date
            full_date_range = pd.date_range(start=df['date'].min(), end=df['date'].max())

            # Reindex the DataFrame to include all dates, filling missing counts with 0
            df = df.set_index('date').reindex(full_date_range, fill_value=0).reset_index()
            df.columns = ['date', 'count']

            # Print the complete data
            print(f"Data for habit '{habit_name}':")
            print(df)

            # Plot the data
            plt.figure(figsize=(10, 6))
            plt.plot(df['date'], df['count'], marker='o', linestyle='-', label=f"'{habit_name}' Counts")
            plt.title(f"Tracker Counts per Date for '{habit_name}'")
            plt.xlabel("Date")
            plt.ylabel("Count")
            plt.xticks(rotation=45)
            plt.grid(True)

            # Force Y-Axis to use only integer values
            plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

            plt.legend()
            plt.tight_layout()
            plt.show()
        else:
            print(f"No tracker entries found for '{habit_name}'.")
    except Exception as e:
        print(f"An error occurred while plotting tracker counts for '{habit_name}': {e}")

def analyze_streak(db, habit_name):
    """
    Analyzes the streak of a given habit based on tracking data.

    Args:
        db: The database connection object.
        habit_name: The name of the habit to analyze.

    Returns:
        str: A report of the habit streak analysis for the user.
    """
    try:
        # Fetch habit details from the database
        habit = db.execute("""
            SELECT creation, interval, period
            FROM counter
            WHERE name = ?
        """, (habit_name,)).fetchone()

        if not habit:
            return f"Habit '{habit_name}' not found in the database."

        creation, interval, period = habit

        # Ensure period is an integer
        period = int(period)

        # Define interval in days dynamically
        interval_days = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,  # Approximation
            "quarterly": 90,  # Approximation
            "yearly": 365
        }.get(interval, 1)  # Default to 1 day if interval not found

        # Fetch tracking data
        tracking_data = db.execute("""
            SELECT date
            FROM tracker
            WHERE counterName = ?
            ORDER BY date ASC
        """, (habit_name,)).fetchall()

        if not tracking_data:
            return f"No tracking data found for habit '{habit_name}'."

        # Convert tracking dates to datetime objects
        track_dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in tracking_data]

        # Initialize variables
        current_streak = 0
        max_streak = 0
        streak_broken = False
        expected_start = datetime.strptime(creation, '%Y-%m-%d')
        today = datetime.now()

        # Evaluate each interval independently, stopping at today's date
        for _ in range(period):
            # Define the current interval's end
            expected_end = expected_start + timedelta(days=interval_days)

            # Stop if the interval's start exceeds today's date
            if expected_start > today:
                break

            # Check if at least one tracking date falls within this interval
            if any(expected_start <= date < expected_end for date in track_dates):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                streak_broken = True
                current_streak = 0  # Reset streak

            # Move to the next interval
            expected_start = expected_end

        # Generate report
        report = f"Habit '{habit_name}':\n"
        report += f"- Current Streak: {current_streak} intervals\n"
        report += f"- Longest Streak: {max_streak} intervals\n"
        report += f"- Total Intervals Checked: {_ + 1}\n"  # _ counts the loops
        report += f"- Tracking Entries: {len(track_dates)}\n"
        if not streak_broken:
            report += "- The habit was maintained consistently without any breaks.\n"
        else:
            report += "- The habit was not maintained consistently; there were breaks in the streak.\n"

        return report

    except sqlite3.Error as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"