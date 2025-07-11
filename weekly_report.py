import pandas as pd
from datetime import datetime

def pace_format(pace_string):
    """Convert pace from mm:ss to float for calculations"""
    parts = pace_string.split(":")
    return round(int(parts[0]) + int(parts[1]) / 60, 2)

def pace_format_back(pace_float):
    """Convert pace from float back to mm:ss format"""
    minutes = int(pace_float)
    seconds = int(round((pace_float - minutes) * 60))
    return f"{minutes}:{seconds:02d}"

def get_current_week():
    """Get the current week number"""
    return datetime.now().isocalendar().week

def display_week_summary(weekly_data, week_num, df_filtered):
    """Display a formatted summary for a specific week"""
    if week_num not in weekly_data.index:
        print(f"No data found for week {week_num}")
        return
    
    week_data = weekly_data.loc[week_num]
    runs_in_week = df_filtered[df_filtered["week"] == week_num]
    
    print(f"\n{'='*50}")
    print(f"WEEK {week_num} SUMMARY")
    print(f"{'='*50}")
    print(f"Total Distance: {week_data['distance']:.2f} km")
    print(f"Number of Runs: {week_data['num_runs']}")
    print(f"Average Pace: {week_data['avg_pace']}")
    print(f"Average Rating: {week_data['rating']:.1f}/10")
    print(f"Average HR: {week_data['avg_hr']:.0f} bpm")
    print(f"Total Ascent: {week_data['total_ascent']:.0f} m")
    
    if week_data['notes']:
        print(f"Notes: {week_data['notes']}")
    
    print(f"\nIndividual Runs:")
    print("-" * 50)
    for _, run in runs_in_week.iterrows():
        print(f"{run['date'].strftime('%Y-%m-%d')}: {run['distance']:.2f}km, "
              f"Rating: {run['rating']}/10")
    print()

def main():
    try:
        df = pd.read_csv("data/runs.csv")
    except FileNotFoundError:
        print("No runs.csv file found. Add some runs first!")
        return
    
    if df.empty:
        print("No runs recorded yet. Add some runs first!")
        return
    
    # Convert date and add week column
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["week"] = df["date"].dt.isocalendar().week
    
    # Convert pace to float for calculations
    df["avg pace"] = df["avg pace"].apply(pace_format)
    
    # Calculate weekly summaries
    weekly = df.groupby("week").agg(
        distance=("distance", "sum"),
        num_runs=("date", "count"),
        rating=("rating", "mean"),
        avg_pace=("avg pace", "mean"),
        avg_hr=("avg hr", "mean"),
        total_ascent=("total ascent", "sum"),
        notes=(
            "notes",
            lambda x: "; ".join([str(n) for n in x if pd.notnull(n) and n != ""]),
        ),
    )
    
    # Convert average pace back to mm:ss format
    weekly["avg_pace"] = weekly["avg_pace"].apply(pace_format_back)
    
    # Get current week
    current_week = get_current_week()
    
    # Display current week by default
    print("Running Data Weekly Report")
    display_week_summary(weekly, current_week, df)
    
    # Interactive menu
    while True:
        print("Options:")
        print("1. Show current week")
        print("2. Show specific week")
        print("3. Show all weeks")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            display_week_summary(weekly, current_week, df)
        elif choice == "2":
            try:
                week_num = int(input("Enter week number: "))
                display_week_summary(weekly, week_num, df)
            except ValueError:
                print("Please enter a valid week number.")
        elif choice == "3":
            print("\nAll Weeks Summary:")
            print("=" * 60)
            print(weekly.to_string())
            print()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.\n")

if __name__ == "__main__":
    main()
