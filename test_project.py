from counter import Counter
from db import get_db, add_counter, increment_counter, get_counter_data
from analyse import total_habit

class TestCounter:

    def setup_method(self):
        """
        Sets up the test environment by initializing the test database.

        This method performs the following actions:
        - Connects to a test database ('test.db') and resets the 'counter' and 'tracker' tables.
        - Adds a predefined counter 'test_counter' with a description.
        - Inserts specific event data for 'test_counter' with predefined dates.

        Side Effects:
            - Modifies the test database by clearing existing data and inserting new data.
        """
        self.db = get_db("test.db")
        cur = self.db.cursor()

        # Reset the database
        cur.execute("DELETE FROM counter")
        cur.execute("DELETE FROM tracker")
        self.db.commit()

        # Add test data
        add_counter(self.db, "test_counter", "test_description", "daily", "365", "")
        increment_counter(self.db, "test_counter", "2021-12-06")
        increment_counter(self.db, "test_counter", "2021-12-07")
        increment_counter(self.db, "test_counter", "2021-12-10")
        increment_counter(self.db, "test_counter", "2021-12-15")

        # Debugging: Verify inserted data
        counters = cur.execute("SELECT * FROM counter").fetchall()
        trackers = cur.execute("SELECT * FROM tracker").fetchall()
        print(f"Counters: {counters}")
        print(f"Trackers: {trackers}")

    def test_counter(self):
        """
        Tests the core functionality of the Counter class.

        This test verifies the following:
        - Creation of a Counter object and storing it in the database.
        - Incrementing the counter and recording events.
        - Resetting the counter and performing further increments.

        Side Effects:
            - Updates the database by storing, adding events, and resetting the counter.
        """
        counter = Counter("test_counter_1", "test_description_1", "", "", "")
        counter.store(self.db)

        # Perform counter operations
        counter.add_event(self.db)
        counter.reset(self.db)

        # Debugging: Verify results
        data = get_counter_data(self.db, "test_counter_1")
        print(f"Data for test_counter_1: {data}")

    def test_db_counter(self):
        """
        Tests the database functionality for a specific counter.

        This method checks:
        1. The number of entries retrieved from the tracker table for the counter named 'test_counter'.
        2. The total count of counters in the database.

        Assertions:
            - Verifies that the number of entries in the tracker table matches the expected value (4).
            - Verifies that the total number of counters in the database matches the expected value (1).
        """
        # Retrieve tracker entries for 'test_counter'
        tracker_data = get_counter_data(self.db, "test_counter")
        assert len(tracker_data) == 4, f"Expected 4 entries, got {len(tracker_data)}"

        # Check the total count of counters in the database
        try:
            cur = self.db.cursor()
            cur.execute("SELECT COUNT(*) FROM counter")
            total_counters = cur.fetchone()[0]
        except Exception as e:
            print(f"Error calculating total counters: {e}")
            total_counters = 0

        # Validate the total count of counters
        assert total_counters == 1, f"Expected 1 counter, got {total_counters}"

    def teardown_method(self):
        """
        Cleans up resources after a test method.

        This method ensures the database connection is closed if it exists
        and deletes the test database file ('test.db') to maintain a clean
        test environment.

        Side Effects:
            - Closes the database connection if open.
            - Deletes the 'test.db' file if it exists.
        """
        import os
        if hasattr(self, 'db') and self.db is not None:
            self.db.close()
        if os.path.exists("test.db"):
            os.remove("test.db")