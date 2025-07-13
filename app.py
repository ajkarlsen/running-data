import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="Running Dashboard",
    page_icon="🏃‍♂️",
    layout="wide"
)

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

def load_data():
    """Load and process running data"""
    try:
        df = pd.read_csv("data/runs.csv")
        if df.empty:
            return None, "No runs recorded yet. Add some runs first!"
        
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
        
        return df, weekly
        
    except FileNotFoundError:
        return None, "No runs.csv file found. Add some runs first!"
    except Exception as e:
        return None, f"Error loading data: {e}"

# Main app
def main():
    st.title("🏃‍♂️ Running Dashboard")
    st.markdown("---")
    
    # Load data
    df, weekly_or_error = load_data()
    
    if df is None:
        st.error(weekly_or_error)
        return
    
    weekly = weekly_or_error
    current_week = get_current_week()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    view_option = st.sidebar.selectbox(
        "Choose View:",
        ["Current Week", "Previous Weeks", "All Weeks", "Individual Runs"]
    )
    
    # Current Week View
    if view_option == "Current Week":
        st.header(f"Week {current_week} Summary")
        
        if current_week in weekly.index:
            week_data = weekly.loc[current_week]
            
            # Create metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Distance", f"{week_data['distance']:.2f} km")
                st.metric("Number of Runs", int(week_data['num_runs']))
            
            with col2:
                st.metric("Average Pace", week_data['avg_pace'])
                st.metric("Average Rating", f"{week_data['rating']:.1f}/10")
            
            with col3:
                st.metric("Average Heart Rate", f"{week_data['avg_hr']:.0f} bpm")
                st.metric("Total Ascent", f"{week_data['total_ascent']:.0f} m")
            
            # Show individual runs for current week with charts
            st.subheader("Individual Runs")
            current_week_runs = df[df["week"] == current_week].copy()
            current_week_runs["avg pace"] = current_week_runs["avg pace"].apply(pace_format_back)
            
            if len(current_week_runs) > 0:
                # Charts for current week
                col1, col2 = st.columns(2)
                
                with col1:
                    # Daily distance bar chart
                    current_week_runs['day_name'] = current_week_runs['date'].dt.strftime('%a')
                    fig_daily = px.bar(current_week_runs, x='day_name', y='distance',
                                     title='Daily Distance This Week',
                                     labels={'distance': 'Distance (km)', 'day_name': 'Day'})
                    fig_daily.update_layout(height=300)
                    st.plotly_chart(fig_daily, use_container_width=True)
                
                with col2:
                    # Pace trend this week (if multiple runs)
                    if len(current_week_runs) > 1:
                        current_week_runs['pace_numeric'] = current_week_runs["avg pace"].apply(pace_format)
                        fig_pace = px.line(current_week_runs, x='date', y='pace_numeric',
                                         title='Pace Trend This Week',
                                         labels={'pace_numeric': 'Pace (min/km)', 'date': 'Date'})
                        fig_pace.update_traces(line_width=3, mode='lines+markers')
                        fig_pace.update_layout(height=300)
                        st.plotly_chart(fig_pace, use_container_width=True)
                    else:
                        # Run type pie chart if only one run or show run type distribution
                        type_counts = current_week_runs['type'].value_counts()
                        if len(type_counts) > 1:
                            fig_type = px.pie(values=type_counts.values, names=type_counts.index,
                                            title='Run Types This Week')
                            fig_type.update_layout(height=300)
                            st.plotly_chart(fig_type, use_container_width=True)
                        else:
                            st.info("Add more runs this week to see pace trends!")
            
            # Individual run details
            
            for _, run in current_week_runs.iterrows():
                with st.expander(f"{run['date'].strftime('%Y-%m-%d')} - {run['type']} ({run['distance']:.2f}km)"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Distance:** {run['distance']:.2f} km")
                        st.write(f"**Pace:** {run['avg pace']}")
                    with col2:
                        st.write(f"**Heart Rate:** {run['avg hr']:.0f} bpm")
                        st.write(f"**Rating:** {run['rating']}/10")
                    with col3:
                        st.write(f"**Ascent:** {run['total ascent']:.0f} m")
                        st.write(f"**Type:** {run['type']}")
                    
                    if pd.notnull(run['notes']) and run['notes'] != "":
                        st.write(f"**Notes:** {run['notes']}")
        else:
            st.info(f"No data found for week {current_week}")
    
    # Specific Week View
    elif view_option == "Previous Weeks":
        st.header("Weekly Summary")
        
        available_weeks = sorted(weekly.index.tolist())
        selected_week = st.selectbox("Select Week:", available_weeks)
        
        if selected_week:
            week_data = weekly.loc[selected_week]
            
            # Create metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Distance", f"{week_data['distance']:.2f} km")
                st.metric("Number of Runs", int(week_data['num_runs']))
            
            with col2:
                st.metric("Average Pace", week_data['avg_pace'])
                st.metric("Average Rating", f"{week_data['rating']:.1f}/10")
            
            with col3:
                st.metric("Average Heart Rate", f"{week_data['avg_hr']:.0f} bpm")
                st.metric("Total Ascent", f"{week_data['total_ascent']:.0f} m")
            
            # Week comparison and charts
            selected_week_runs = df[df["week"] == selected_week].copy()
            selected_week_runs["avg pace"] = selected_week_runs["avg pace"].apply(pace_format_back)
            
            if len(selected_week_runs) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Daily distance for selected week
                    selected_week_runs['day_name'] = selected_week_runs['date'].dt.strftime('%a')
                    fig_daily = px.bar(selected_week_runs, x='day_name', y='distance',
                                     title=f'Daily Distance - Week {selected_week}',
                                     labels={'distance': 'Distance (km)', 'day_name': 'Day'})
                    fig_daily.update_layout(height=300)
                    st.plotly_chart(fig_daily, use_container_width=True)
                
                with col2:
                    # Pace per run in selected week
                    if len(selected_week_runs) > 1:
                        selected_week_runs['pace_numeric'] = selected_week_runs["avg pace"].apply(pace_format)
                        fig_pace = px.line(selected_week_runs, x='date', y='pace_numeric',
                                         title=f'Pace Trend - Week {selected_week}',
                                         labels={'pace_numeric': 'Pace (min/km)', 'date': 'Date'})
                        fig_pace.update_traces(line_width=3, mode='lines+markers')
                        fig_pace.update_layout(height=300)
                        st.plotly_chart(fig_pace, use_container_width=True)
                    else:
                        # Show week comparison if only one run
                        available_weeks_sorted = sorted(weekly.index.tolist())
                        if len(available_weeks_sorted) > 1:
                            current_week_idx = available_weeks_sorted.index(selected_week)
                            if current_week_idx > 0:
                                prev_week = available_weeks_sorted[current_week_idx - 1]
                                prev_week_data = weekly.loc[prev_week]
                                
                                st.subheader("vs Previous Week")
                                distance_change = week_data['distance'] - prev_week_data['distance']
                                runs_change = week_data['num_runs'] - prev_week_data['num_runs']
                                
                                st.metric("Distance Change", f"{distance_change:+.1f} km")
                                st.metric("Runs Change", f"{runs_change:+.0f} runs")
                
                # Show individual runs for the week
                st.subheader(f"Runs in Week {selected_week}")
                for _, run in selected_week_runs.iterrows():
                    with st.expander(f"{run['date'].strftime('%Y-%m-%d')} - {run['type']} ({run['distance']:.2f}km)"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Distance:** {run['distance']:.2f} km")
                            st.write(f"**Pace:** {run['avg pace']}")
                        with col2:
                            st.write(f"**Heart Rate:** {run['avg hr']:.0f} bpm")
                            st.write(f"**Rating:** {run['rating']}/10")
                        with col3:
                            st.write(f"**Ascent:** {run['total ascent']:.0f} m")
                            st.write(f"**Type:** {run['type']}")
                        
                        if pd.notnull(run['notes']) and run['notes'] != "":
                            st.write(f"**Notes:** {run['notes']}")
    
    # All Weeks View
    elif view_option == "All Weeks":
        st.header("All Weeks Summary")
        
        # Charts for all weeks overview
        col1, col2 = st.columns(2)
        
        with col1:
            # Weekly distance bar chart
            weekly_plot = weekly.reset_index()
            fig_weekly_dist = px.bar(weekly_plot, x='week', y='distance',
                                   title='Weekly Distance Trend',
                                   labels={'distance': 'Total Distance (km)', 'week': 'Week'})
            fig_weekly_dist.update_layout(height=400)
            st.plotly_chart(fig_weekly_dist, use_container_width=True)
        
        with col2:
            # Rolling average pace line chart
            weekly_plot['avg_pace_numeric'] = weekly_plot['avg_pace'].apply(pace_format)
            fig_pace_trend = px.line(weekly_plot, x='week', y='avg_pace_numeric',
                                   title='Average Pace Trend',
                                   labels={'avg_pace_numeric': 'Avg Pace (min/km)', 'week': 'Week'})
            fig_pace_trend.update_traces(line_width=3, mode='lines+markers')
            fig_pace_trend.update_layout(height=400)
            st.plotly_chart(fig_pace_trend, use_container_width=True)
        
        # Additional charts
        col3, col4 = st.columns(2)
        
        with col3:
            # Weekly distance vs average pace scatter
            fig_scatter = px.scatter(weekly_plot, x='distance', y='avg_pace_numeric',
                                   size='num_runs', hover_data=['week'],
                                   title='Weekly Distance vs Pace',
                                   labels={'distance': 'Total Distance (km)', 'avg_pace_numeric': 'Avg Pace (min/km)'})
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col4:
            # Weekly elevation trend
            fig_elevation = px.line(weekly_plot, x='week', y='total_ascent',
                                  title='Weekly Elevation Gain',
                                  labels={'total_ascent': 'Total Ascent (m)', 'week': 'Week'})
            fig_elevation.update_traces(line_width=3, mode='lines+markers')
            fig_elevation.update_layout(height=400)
            st.plotly_chart(fig_elevation, use_container_width=True)
        
        # Data table
        st.subheader("Weekly Summary Table")
        # Prepare data for display
        display_weekly = weekly.copy()
        display_weekly = display_weekly.reset_index()
        display_weekly.columns = ['Week', 'Distance (km)', 'Runs', 'Avg Rating', 'Avg Pace', 'Avg HR', 'Total Ascent (m)']
        
        # Format numeric columns with proper type handling
        display_weekly['Distance (km)'] = display_weekly['Distance (km)'].round(2)
        display_weekly['Avg Rating'] = display_weekly['Avg Rating'].round(2)
        display_weekly['Avg HR'] = display_weekly['Avg HR'].round(0).astype(int)
        display_weekly['Total Ascent (m)'] = display_weekly['Total Ascent (m)'].round(0).astype(int)
        
        # Avg Pace is already in mm:ss format from the weekly dataframe, no conversion needed
        
        st.dataframe(display_weekly, use_container_width=True)
    
    # Individual Runs View
    elif view_option == "Individual Runs":
        st.header("All Individual Runs")
        
        # Prepare data for display
        display_runs = df.copy()
        display_runs["avg pace"] = display_runs["avg pace"].apply(pace_format_back)
        display_runs = display_runs[['date', 'distance', 'avg pace', 'avg hr', 'total ascent', 'rating', 'type', 'notes']]
        display_runs.columns = ['Date', 'Distance (km)', 'Avg Pace', 'Avg HR', 'Total Ascent (m)', 'Rating', 'Type', 'Notes']
        
        # Format numeric columns
        display_runs['Distance (km)'] = pd.to_numeric(display_runs['Distance (km)'], errors='coerce').round(2)
        display_runs['Avg HR'] = pd.to_numeric(display_runs['Avg HR'], errors='coerce').round(0).astype('Int64')
        display_runs['Total Ascent (m)'] = pd.to_numeric(display_runs['Total Ascent (m)'], errors='coerce').round(0).astype('Int64')
        
        st.dataframe(display_runs, use_container_width=True)

if __name__ == "__main__":
    main()