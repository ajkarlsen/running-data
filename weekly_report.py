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
    
    print(f"\n{'='*60}")
    print(f"WEEK {week_num} SUMMARY".center(60))
    print(f"{'='*60}")
    
    # Create a nicely formatted summary table
    print(f"{'Total Distance:':<20} {week_data['distance']:.2f} km")
    print(f"{'Number of Runs:':<20} {week_data['num_runs']}")
    print(f"{'Average Pace:':<20} {week_data['avg_pace']}")
    print(f"{'Average Rating:':<20} {week_data['rating']:.1f}/10")
    print(f"{'Average Heart Rate:':<20} {week_data['avg_hr']:.0f} bpm")
    print(f"{'Total Ascent:':<20} {week_data['total_ascent']:.0f} m")
    
    print(f"\n{'INDIVIDUAL RUNS'.center(60)}")
    print("-" * 60)
    
    for _, run in runs_in_week.iterrows():
        date_str = run['date'].strftime('%Y-%m-%d')
        run_type = run.get('type', 'Unknown')
        
        print(f"{date_str} | {run['distance']:.2f}km | {run_type} | Rating: {run['rating']}/10")
        
        # Show notes if they exist
        if pd.notnull(run['notes']) and run['notes'] != "":
            print(f"    Notes: {run['notes']}")
    
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
            print("\nALL WEEKS SUMMARY")
            print("=" * 70)
            
            # Create a nicely formatted table for all weeks
            print(f"{'Week':<6} {'Distance':<10} {'Runs':<6} {'Avg Pace':<10} {'Avg Rating':<12} {'Avg HR':<8} {'Total Ascent':<12}")
            print("-" * 80)
            
            for week_num in sorted(weekly.index):
                week_data = weekly.loc[week_num]
                print(f"{week_num:<6} {week_data['distance']:<10.2f} {week_data['num_runs']:<6} "
                      f"{week_data['avg_pace']:<10} {week_data['rating']:<12.1f} {week_data['avg_hr']:<8.0f} "
                      f"{week_data['total_ascent']:<12.0f}")
            
            print()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.\n")

if __name__ == "__main__":
    main()
