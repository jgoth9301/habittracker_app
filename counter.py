from db import add_counter, increment_counter
from datetime import datetime

class Counter:
    """
    A class to represent a counter for tracking events.

    Attributes:
        name (str): The name of the counter.
        description (str): A brief description of the counter's purpose.
        interval (str): The interval for the counter (e.g., daily, weekly).
        creation (str): The creation date of the counter in 'YYYY-MM-DD' format. Defaults to the current date.
        count (int): The current count of events. Defaults to 0.

    Args:
        name (str): The name of the counter.
        description (str): A description of the counter.
        interval (str): The interval type for the counter.
        creation (str, optional): The creation timestamp. Defaults to the current date.
    """

    def __init__(self, name: str, description: str, interval: str, period: str, creation=None):
        self.name = name
        self.description = description
        self.interval = interval
        self.period = period
        self.creation = creation or datetime.now().strftime('%Y-%m-%d')
        self.count = 0

    def delete(self, db):
        """
        Deletes the counter and all associated tracking data from the database.

        Args:
            db: The database connection object.

        Raises:
            Exception: If an error occurs during the database operation.

        Side Effects:
            - Removes the counter from the 'counter' table.
            - Removes all associated entries from the 'tracker' table.
            - Commits the changes to the database.
            - Prints a success or error message to the console.
        """
        try:
            cur = db.cursor()

            # Delete the counter from the counter table
            cur.execute("DELETE FROM counter WHERE name = ?", (self.name,))
            counter_deleted = cur.rowcount  # Number of deleted rows in counter

            # Delete associated entries from the tracker table
            cur.execute("DELETE FROM tracker WHERE counterName = ?", (self.name,))
            tracker_deleted = cur.rowcount  # Number of deleted rows in tracker

            db.commit()

            # Provide confirmation based on deletion results
            if counter_deleted > 0:
                print(f"Counter '{self.name}' deleted successfully.")
            if tracker_deleted > 0:
                print(f"Deleted {tracker_deleted} associated tracking entries for counter '{self.name}'.")
            elif counter_deleted == 0:
                print(f"Counter '{self.name}' does not exist in the database.")
        except Exception as e:
            # Handle any exceptions and provide feedback
            print(f"An error occurred while deleting counter '{self.name}': {e}")
        finally:
            # Close the cursor to ensure cleanup
            cur.close()

    def reset(self, db):
        """
        Resets the counter by deleting all associated tracking data
        from the 'tracker' table, while keeping the counter in the database.

        Args:
            db: The database connection object.

        Side Effects:
            - Removes all entries in the 'tracker' table associated with this counter.
            - Commits the changes to the database.
            - Prints a success or error message to the console.
        """
        try:
            cur = db.cursor()

            # Delete associated entries from the tracker table
            cur.execute("DELETE FROM tracker WHERE counterName = ?", (self.name,))
            tracker_deleted = cur.rowcount  # Number of deleted rows in tracker

            # Delete the counter itself
            cur.execute("DELETE FROM counter WHERE name = ?", (self.name,))
            counter_deleted = cur.rowcount  # Number of deleted rows in counter

            db.commit()

            # Provide confirmation based on deletion results
            if counter_deleted > 0:
                print(f"Counter '{self.name}' deleted successfully.")
            else:
                print(f"Counter '{self.name}' does not exist in the database.")

            if tracker_deleted > 0:
                print(f"Deleted {tracker_deleted} associated tracking entries for counter '{self.name}'.")
        except Exception as e:
            # Handle any exceptions and provide feedback
            print(f"An error occurred while deleting counter '{self.name}': {e}")
        finally:
            # Close the cursor to ensure cleanup
            cur.close()

    def store(self, db):
        """
        Store the counter in the database.

        Args:
            db: The database connection object.
        """
        add_counter(db, self.name, self.description, self.interval, self.period, self.creation)

    def add_event(self, db, date: str = None):
        """
        Add an event for this counter to the database.

        Args:
            db: The database connection object.
            date (str): The date of the event (in 'YYYY-MM-DD' format). Defaults to today's date.
        """
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime('%Y-%m-%d')

        increment_counter(db, self.name, date)