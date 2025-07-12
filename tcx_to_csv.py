import xml.etree.ElementTree as ET
import pandas as pd
import sys
import os

def parse_tcx_to_csv(tcx_file_path, csv_file_path):
    """
    Parse a TCX file and convert it to CSV format matching Garmin Connect export format.
    
    Args:
        tcx_file_path (str): Path to the input TCX file
        csv_file_path (str): Path to the output CSV file
    """
    try:
        # Parse the XML file
        tree = ET.parse(tcx_file_path)
        root = tree.getroot()
        
        # Define XML namespaces
        ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        
        # Find all laps in the activity
        laps = root.findall('.//tcx:Lap', ns)
        
        if not laps:
            print("No laps found in the TCX file")
            return
        
        # Initialize data list
        data = []
        cumulative_time = 0
        
        # Process each lap
        for i, lap in enumerate(laps, 1):
            # Get lap data
            total_time = float(lap.find('tcx:TotalTimeSeconds', ns).text)
            distance = float(lap.find('tcx:DistanceMeters', ns).text) / 1000  # Convert to km
            calories = int(lap.find('tcx:Calories', ns).text)
            
            # Heart rate data
            avg_hr_elem = lap.find('tcx:AverageHeartRateBpm/tcx:Value', ns)
            max_hr_elem = lap.find('tcx:MaximumHeartRateBpm/tcx:Value', ns)
            
            avg_hr = int(avg_hr_elem.text) if avg_hr_elem is not None else ""
            max_hr = int(max_hr_elem.text) if max_hr_elem is not None else ""
            
            # Calculate ascent for this lap
            lap_ascent = calculate_ascent(lap, ns)
            
            # Calculate cumulative time
            cumulative_time += total_time
            
            # Format time strings
            time_str = format_seconds_to_time(total_time)
            cumulative_time_str = format_seconds_to_time(cumulative_time)
            
            # Calculate pace (min/km)
            pace_seconds = total_time / distance if distance > 0 else 0
            pace_str = format_seconds_to_pace(pace_seconds)
            
            # Create lap data dictionary
            lap_data = {
                'Laps': str(i),
                'Time': time_str,
                'Cumulative Time': cumulative_time_str,
                'Distancekm': f"{distance:.2f}",
                'Avg Pacemin/km': pace_str,
                'Avg GAPmin/km': pace_str,  # Using same as pace for now
                'Avg HRbpm': str(avg_hr),
                'Max HRbpm': str(max_hr),
                'Total Ascentm': f"{lap_ascent:.2f}" if lap_ascent > 0 else "",  # Using calculated ascent
                'Total Descentm': "",  # Not available in basic TCX
                'Avg PowerW': "",  # Not available in basic TCX
                'Avg W/kg': "",  # Not available in basic TCX
                'Max PowerW': "",  # Not available in basic TCX
                'Max W/kg': "",  # Not available in basic TCX
                'Avg Run Cadencespm': "",  # Not available in basic TCX
                'Avg Ground Contact Timems': "",  # Not available in basic TCX
                'Avg GCT Balance%': "",  # Not available in basic TCX
                'Avg Stride Lengthm': "",  # Not available in basic TCX
                'Avg Vertical Oscillationcm': "",  # Not available in basic TCX
                'Avg Vertical Ratio%': "",  # Not available in basic TCX
                'CaloriesC': str(calories),
                'Avg Temperature': "",  # Not available in basic TCX
                'Best Pacemin/km': pace_str,  # Using avg pace for now
                'Max Run Cadencespm': "",  # Not available in basic TCX
                'Moving Time': time_str,  # Using total time for now
                'Avg Moving Pacemin/km': pace_str,  # Using avg pace for now
                'Avg Step Speed Losscm/s': "",  # Not available in basic TCX
                'Avg Step Speed Loss Percent%': ""  # Not available in basic TCX
            }
            
            data.append(lap_data)
        
        # Create summary row
        total_distance = sum(float(row['Distancekm']) for row in data)
        total_calories = sum(int(row['CaloriesC']) for row in data if row['CaloriesC'])
        
        # Total ascent for summary
        total_ascent = sum(float(row['Total Ascentm']) for row in data if row['Total Ascentm'])
        
        # Calculate average pace for summary
        total_time_seconds = cumulative_time
        avg_pace_seconds = total_time_seconds / total_distance if total_distance > 0 else 0
        avg_pace_str = format_seconds_to_pace(avg_pace_seconds)
        
        # Calculate average heart rate
        hr_values = [int(row['Avg HRbpm']) for row in data if row['Avg HRbpm']]
        avg_hr = int(sum(hr_values) / len(hr_values)) if hr_values else ""
        max_hr = max(int(row['Max HRbpm']) for row in data if row['Max HRbpm']) if any(row['Max HRbpm'] for row in data) else ""
        
        summary_data = {
            'Laps': 'Summary',
            'Time': format_seconds_to_time(total_time_seconds),
            'Cumulative Time': format_seconds_to_time(total_time_seconds),
            'Distancekm': f"{total_distance:.2f}",
            'Avg Pacemin/km': avg_pace_str,
            'Avg GAPmin/km': avg_pace_str,
            'Avg HRbpm': str(avg_hr),
            'Max HRbpm': str(max_hr),
            'Total Ascentm': f"{total_ascent:.2f}" if total_ascent > 0 else "", # Using total ascent
            'Total Descentm': "",
            'Avg PowerW': "",
            'Avg W/kg': "",
            'Max PowerW': "",
            'Max W/kg': "",
            'Avg Run Cadencespm': "",
            'Avg Ground Contact Timems': "",
            'Avg GCT Balance%': "",
            'Avg Stride Lengthm': "",
            'Avg Vertical Oscillationcm': "",
            'Avg Vertical Ratio%': "",
            'CaloriesC': str(total_calories),
            'Avg Temperature': "",
            'Best Pacemin/km': "",
            'Max Run Cadencespm': "",
            'Moving Time': format_seconds_to_time(total_time_seconds),
            'Avg Moving Pacemin/km': avg_pace_str,
            'Avg Step Speed Losscm/s': "",
            'Avg Step Speed Loss Percent%': ""
        }
        
        data.append(summary_data)
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(data)
        df.to_csv(csv_file_path, index=False, quoting=1)  # quoting=1 means QUOTE_ALL
        
        print(f"Successfully converted {tcx_file_path} to {csv_file_path}")
        print(f"Processed {len(data)-1} laps")
        
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    except Exception as e:
        print(f"Error converting TCX to CSV: {e}")

def format_seconds_to_time(seconds):
    """Convert seconds to MM:SS.s format"""
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:04.1f}"

def format_seconds_to_pace(seconds):
    """Convert seconds per km to M:SS pace format"""
    if seconds == 0:
        return ""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}:{remaining_seconds:02d}"

def calculate_ascent(lap, ns):
    """
    Calculate total ascent for a lap by analyzing trackpoint altitude data.
    
    Args:
        lap: XML lap element
        ns: XML namespace dictionary
    
    Returns:
        float: Total ascent in meters
    """
    trackpoints = lap.findall('.//tcx:Trackpoint', ns)
    
    if len(trackpoints) < 2:
        return 0.0
    
    total_ascent = 0.0
    previous_altitude = None
    
    for trackpoint in trackpoints:
        altitude_elem = trackpoint.find('tcx:AltitudeMeters', ns)
        
        if altitude_elem is not None:
            current_altitude = float(altitude_elem.text)
            
            if previous_altitude is not None and current_altitude > previous_altitude:
                total_ascent += current_altitude - previous_altitude
            
            previous_altitude = current_altitude
            
    return total_ascent

def main():
    if len(sys.argv) == 1:
        # No arguments - run batch conversion
        print("No arguments provided. Running batch conversion of all TCX files...")
        batch_convert_tcx_files()
    elif len(sys.argv) == 2:
        if sys.argv[1] == "--batch":
            # Batch conversion with explicit flag
            batch_convert_tcx_files()
        else:
            print("Usage: python tcx_to_csv.py <input_tcx_file> <output_csv_file>")
            print("   or: python tcx_to_csv.py --batch")
            print("   or: python tcx_to_csv.py (for automatic batch conversion)")
            sys.exit(1)
    elif len(sys.argv) == 3:
        # Single file conversion
        tcx_file = sys.argv[1]
        csv_file = sys.argv[2]
        
        # Check if input file exists
        if not os.path.exists(tcx_file):
            print(f"Error: Input file '{tcx_file}' not found")
            sys.exit(1)
        
        # Check if input file is a TCX file
        if not tcx_file.lower().endswith('.tcx'):
            print("Warning: Input file doesn't have .tcx extension")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(csv_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Convert TCX to CSV
        parse_tcx_to_csv(tcx_file, csv_file)
    else:
        print("Usage: python tcx_to_csv.py <input_tcx_file> <output_csv_file>")
        print("   or: python tcx_to_csv.py --batch")
        print("   or: python tcx_to_csv.py (for automatic batch conversion)")
        sys.exit(1)

def batch_convert_tcx_files(tcx_dir='raw_tcx', csv_dir='raw'):
    """
    Convert all TCX files in a directory to CSV format, skipping already converted files.
    
    Args:
        tcx_dir (str): Directory containing TCX files
        csv_dir (str): Directory to save CSV files
    """
    if not os.path.exists(tcx_dir):
        print(f"TCX directory '{tcx_dir}' not found")
        return
    
    # Create CSV directory if it doesn't exist
    os.makedirs(csv_dir, exist_ok=True)
    
    # Get all TCX files
    tcx_files = [f for f in os.listdir(tcx_dir) if f.lower().endswith('.tcx')]
    
    if not tcx_files:
        print(f"No TCX files found in '{tcx_dir}'")
        return
    
    print(f"Found {len(tcx_files)} TCX files")
    
    converted_count = 0
    skipped_count = 0
    
    for tcx_file in sorted(tcx_files):
        tcx_path = os.path.join(tcx_dir, tcx_file)
        
        # Create corresponding CSV filename
        csv_filename = tcx_file.replace('.tcx', '.csv')
        csv_path = os.path.join(csv_dir, csv_filename)
        
        # Check if CSV already exists
        if os.path.exists(csv_path):
            print(f"Skipping {tcx_file} - CSV already exists")
            skipped_count += 1
            continue
        
        print(f"Converting {tcx_file} to {csv_filename}")
        
        try:
            parse_tcx_to_csv(tcx_path, csv_path)
            converted_count += 1
        except Exception as e:
            print(f"Error converting {tcx_file}: {e}")
            continue
    
    print("\nBatch conversion complete!")
    print(f"Converted: {converted_count} files")
    print(f"Skipped: {skipped_count} files")
    print(f"Total processed: {len(tcx_files)} files")

if __name__ == "__main__":
    main()
