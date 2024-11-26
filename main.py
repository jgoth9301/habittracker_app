import questionary
from db import get_db, get_predefined_habits, get_existing_habits, initial_load_tracker, get_existing_habits_short
from counter import Counter
from analyse import total_habit, total_tracker, total_tracker_habit, plot_tracker_counts, analyze_streak


def cli():
    global datetime
    db = get_db()
    cursor = db.cursor()
    initial_load_tracker(db.cursor())  # Initial-Load durchführen
    db.commit()
    ready = questionary.confirm("Are you ready?").ask()
    if ready:
        print("Great! Let's proceed.")
    else:
        print("Exiting CLI. Goodbye!")
        return  # Beenden der Funktion, wenn der Benutzer "No" wählt

    # Loop
    stop = False
    while not stop:

        choice = questionary.select(
            "What you want to do?",
            choices=["Habit Administration", "Habit Tracking", "Habit Analysis", "Exit"]
        ).ask()

        if choice == "Habit Administration":
            choice = questionary.select(
                "What you want to do?",
                choices=["Creation of a new habit", "Selection of a predefined habit", "Delete existing habit", "Exit"]
            ).ask()

            if choice == "Creation of a new habit":
                name = questionary.text("What is the name of your habit?").ask()

                # Check if the name is valid
                if not name:
                    print("The habit name cannot be empty. Please try again.")
                    return

                # Check if the name already exists in the table
                existing_counter = db.execute("SELECT name FROM counter WHERE LOWER(name) = LOWER(?)",
                                              (name,)).fetchone()

                if existing_counter:
                    print(f"A habit with the name '{name}' already exists. Please choose a different name.")
                else:
                    description = questionary.text("What is the description of your habit?").ask()
                    interval = questionary.select(
                        "What is the interval of your counter?",
                        choices=["daily", "weekly", "monthly", "quarterly", "yearly"],
                    ).ask()
                    period = questionary.text(
                        "Over what period would you like to track your habit (based on your chosen interval)?").ask()

                    # Validate period input
                    try:
                        period = int(period)
                        if period <= 0:
                            print("The period must be a positive integer.")
                            return
                    except ValueError:
                        print("Invalid input. The period must be a number.")
                        return

                    creation = datetime.now().strftime('%Y-%m-%d')

                    # Create and store the counter
                    counter = Counter(name, description, interval, period, creation)
                    counter.store(db)

                db.commit()

            if choice == "Selection of a predefined habit":
                # Fetch predefined habits from the database or a predefined list
                predefined_habits = get_predefined_habits(db)

                if not predefined_habits:
                    print("No predefined habits available. Please add predefined habits first.")
                else:
                    # Ask the user to select a predefined habit
                    selected_habit = questionary.select(
                        "Please select one of the predefined habits:",
                        choices=predefined_habits  # Dynamic list of habits
                    ).ask()

                    if selected_habit:
                        # Extract the habit name (split at the first delimiter, if concatenated)
                        habit_name = selected_habit.split(" - ")[0] if " - " in selected_habit else selected_habit

                        try:
                            # Retrieve habit details from the predefinedHabits table
                            habit_details = db.execute(
                                "SELECT name, description, interval FROM predefinedHabits WHERE name = ?", (habit_name,)
                            ).fetchone()

                            if habit_details:
                                name, description, interval = habit_details
                                period = questionary.text(
                                    "Over what period would you like to track your habit (based on your chosen interval)?"
                                ).ask()

                                # Validate period input
                                try:
                                    period = int(period)
                                    if period <= 0:
                                        print("The period must be a positive integer.")
                                        return
                                except ValueError:
                                    print("Invalid input. The period must be a number.")
                                    return

                                creation = datetime.now().strftime('%Y-%m-%d')

                                # Check if the name already exists in the counter table
                                db.execute("PRAGMA foreign_keys = ON;")
                                existing_counter = db.execute(
                                    "SELECT name FROM counter WHERE LOWER(name) = LOWER(?)", (name,)
                                ).fetchone()
                                if existing_counter:
                                    print(
                                        f"A counter with the name '{name}' already exists. Please choose a different name.")
                                else:
                                    # Create and store the counter
                                    counter = Counter(name, description, interval, period, creation)
                                    counter.store(db)
                                    print(f"Habit '{name}' has been successfully added to your tracker.")
                            else:
                                print(f"Error: Habit '{habit_name}' not found in the database.")
                        except sqlite3.Error as e:
                            print(f"Database error: {e}")
                    else:
                        print("No habit was selected. Exiting.")
                db.commit()

            if choice == "Delete existing habit":
                # Fetch existing habits from the database or a predefined list
                existing_habits = get_existing_habits(db)

                if not existing_habits:
                    print("No existing habits available.")
                else:
                    # Ask the user to select an existing habit
                    selected_habit = questionary.select(
                        "Please select one of the existing habits:",
                        choices=existing_habits  # Dynamic list of habits
                    ).ask()

                    # Extract the habit name (if concatenated, split at the first delimiter)
                    habit_name = selected_habit.split(" - ")[0]

                    # Retrieve habit details (name, description, interval) from the database
                    habit_details = db.execute(
                        "SELECT name, description, interval, period, creation FROM counter WHERE name = ?",
                        (habit_name,)
                    ).fetchone()

                    if habit_details:
                        name, description, interval, period, creation = habit_details

                        # Add confirmation step
                        confirm = questionary.confirm(
                            f"Are you sure you want to delete the habit '{name}' and all related tracking data? This action cannot be undone."
                        ).ask()

                        if confirm:
                            # Create a Counter object and delete it
                            counter = Counter(name, description, interval, period, creation)
                            counter.delete(db)
                        else:
                            print("Deletion canceled.")
                    else:
                        print(f"Error: Habit '{habit_name}' not found in the database.")
                db.commit()

        elif choice == "Habit Tracking":
            choice = questionary.select(
                "What you want to do?",
                choices=["Tracking", "Reset Tracker", "Exit"]
            ).ask()

            if choice == "Tracking":
                # Check if `habit_names` has values
                habit_names = get_existing_habits_short(db)
                if not habit_names:
                    print("No habits found in the database.")
                else:
                    # Ask the user to select a habit only if `habit_names` is not empty
                    name = questionary.select(
                        "Select the name of the habit you like to track:",
                        choices=habit_names
                    ).ask()

                    if not name:
                        print("No habit selected. Aborting tracking.")
                        return

                    # Fetch habit details from the database
                    habit_details = db.execute(
                        "SELECT name, description, interval, period, creation FROM counter WHERE name = ?",
                        (name,)
                    ).fetchone()

                    if habit_details:
                        # Initialize the Counter object with retrieved data
                        name, description, interval, period, creation = habit_details
                        counter = Counter(name, description, interval, period, creation)

                        # Check if an entry already exists for today
                        from datetime import datetime
                        today = datetime.now().strftime('%Y-%m-%d')

                        existing_entry = db.execute(
                            "SELECT 1 FROM tracker WHERE date = ? AND counterName = ?",
                            (today, name)
                        ).fetchone()

                        if existing_entry:
                            print(f"An entry for '{name}' already exists for {today}.")
                        else:
                            # Add the event since it does not exist
                            counter.add_event(db)
                            db.commit()  # Commit only after an event is added
                            print(f"A new entry for '{name}' on {today} was successfully created.")
                    else:
                        print(f"Error: Habit '{name}' not found in the database.")

            if choice == "Reset Tracker":
                # Fetch existing habits from the database or a predefined list
                existing_habits = get_existing_habits_short(db)

                if not existing_habits:
                    print("No existing habits available.")
                else:
                    # Ask the user to select an existing habit
                    selected_habit = questionary.select(
                        "Please select one of the existing habits:",
                        choices=existing_habits  # Dynamic list of habits
                    ).ask()

                    # Handle case where user cancels the selection
                    if not selected_habit:
                        print("No habit selected. Aborting reset.")
                        return

                    # Retrieve habit details (name, description, interval, period, creation) from the database
                    habit_details = db.execute(
                        "SELECT name, description, interval, period, creation FROM counter WHERE name = ?",
                        (selected_habit,)  # Pass the selected habit as a scalar value
                    ).fetchone()

                    if habit_details:
                        # Unpack habit details
                        name, description, interval, period, creation = habit_details

                        # Add confirmation step
                        confirm = questionary.confirm(
                            f"Are you sure you want to delete all tracking data related to habit '{name}'? This action cannot be undone."
                        ).ask()

                        if confirm:
                            # Create a Counter object and reset the tracker
                            counter = Counter(name, description, interval, period, creation)
                            counter.reset(db)

                            # Commit the changes
                            db.commit()
                            print(f"All tracking data for habit '{name}' has been successfully deleted.")
                        else:
                            print("Reset canceled.")
                    else:
                        print(f"Error: Habit '{selected_habit}' not found in the database.")
                db.commit()

        if choice == "Habit Analysis":
            choice = questionary.select(
                "What you want to do?",
                choices=["Habit count total", "Tracker count total", "Tracker count per habit", "Tracker count per habit - visualized", "Streak analysis", "Exit"]
            ).ask()

            if choice == "Habit count total":
                total_count = total_habit(db)
                print(f"Total number of habit entries: {total_count}")

            if choice == "Tracker count total":
                total_count = total_tracker(db)
                print(f"Total number of tracker entries: {total_count}")

            if choice == "Tracker count per habit":
                # Fetch existing habits from the database or a predefined list
                existing_habits = get_existing_habits_short(db)

                if not existing_habits:
                    print("No existing habits available.")
                else:
                    # Ask the user to select an existing habit
                    selected_habit = questionary.select(
                        "Please select one of the existing habits:",
                        choices=existing_habits  # Dynamic list of habits
                    ).ask()

                    if selected_habit:
                        # Extract only the habit name if additional info exists
                        selected_habit_name = selected_habit.split(" - ")[0]

                        total_count = total_tracker_habit(db, selected_habit_name)  # Habit-Name übergeben
                        print(f"Total number of tracker entries for '{selected_habit_name}': {total_count}")

                    else:
                        print("No habit selected. Exiting.")

            if choice == "Tracker count per habit - visualized":
                # Fetch existing habits from the database or a predefined list
                existing_habits = get_existing_habits_short(db)

                if not existing_habits:
                    print("No existing habits available.")
                else:
                    # Ask the user to select an existing habit
                    selected_habit = questionary.select(
                        "Please select one of the existing habits:",
                        choices=existing_habits  # Dynamic list of habits
                    ).ask()

                    if selected_habit:
                        # Extract only the habit name if additional info exists
                        selected_habit_name = selected_habit.split(" - ")[0]

                        total_count = total_tracker_habit(db, selected_habit_name)  # Habit-Name übergeben
                        print(f"Total number of tracker entries for '{selected_habit_name}': {total_count}")

                        # Call the function to plot tracker counts
                        plot_tracker_counts(db, selected_habit_name)
                    else:
                        print("No habit selected. Exiting.")

            if choice == "Streak analysis":
                # Fetch existing habits from the database or a predefined list
                existing_habits = get_existing_habits_short(db)

                if not existing_habits:
                    print("No existing habits available.")
                else:
                    # Ask the user to select an existing habit
                    selected_habit = questionary.select(
                        "Please select one of the existing habits:",
                        choices=existing_habits  # Dynamic list of habits
                    ).ask()

                    if selected_habit:
                        # Extract only the habit name if additional info exists
                        selected_habit_name = selected_habit.split(" - ")[
                            0] if " - " in selected_habit else selected_habit

                        # Total tracker entries
                        total_count = total_tracker_habit(db, selected_habit_name)  # Habit-Name übergeben
                        print(f"Total number of tracker entries for '{selected_habit_name}': {total_count}")

                        # Call the function to analyze streaks
                        result = analyze_streak(db, selected_habit_name)
                        print(result)  # Display the streak analysis report
                    else:
                        print("No habit selected. Exiting.")

        else:
            print("Bye!")
            stop = True

if __name__ == '__main__':
    cli()