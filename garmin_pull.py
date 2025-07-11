from garminconnect import Garmin
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import zipfile
import tempfile

load_dotenv()

email = os.getenv("GARMIN_EMAIL")
password = os.getenv("GARMIN_PASSWORD")

LAST_DOWNLOAD_FILE = 'last_download.txt'

def get_activity_date_from_tcx(tcx_content):
    """Extract start date from TCX content"""
    try:
        # Look for the Activity Id which contains the start time
        import xml.etree.ElementTree as ET
        root = ET.fromstring(tcx_content)
        
        # Define namespace
        ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        
        # Find the Activity Id (which is the start time)
        activity_id = root.find('.//tcx:Activity/tcx:Id', ns)
        if activity_id is not None:
            # Parse the datetime string (format: 2025-07-11T10:38:12.000Z)
            dt = datetime.fromisoformat(activity_id.text.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        
        return None
    except Exception as e:
        print(f"Error extracting date from TCX: {e}")
        return None

def download_tcx_files(client):
    """Download TCX files for new activities since last download"""
    try:
        # Get the last download date
        last_download = get_last_download_date()
        end_date = datetime.now()
        
        # Add one day buffer to ensure we don't miss any activities
        start_date = last_download - timedelta(days=1)
        
        print(f"Checking for new activities from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get activities for the date range
        activities = client.get_activities_by_date(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if not activities:
            print("No activities found in the specified date range")
            save_last_download_date()  # Update the date even if no activities found
            return
        
        print(f"Found {len(activities)} total activities")
        
        # Get already downloaded activity IDs
        downloaded_ids = get_downloaded_activity_ids()
        
        # Create raw_tcx directory if it doesn't exist
        os.makedirs('raw_tcx', exist_ok=True)
        
        new_downloads = 0
        
        # Download each activity as TCX
        for activity in activities:
            activity_id = activity['activityId']
            activity_name = activity.get('activityName', 'Unknown')
            activity_type = activity.get('activityType', {}).get('typeKey', 'Unknown')
            
            # Only download running activities
            if activity_type.lower() not in ['running', 'trail_running', 'treadmill_running']:
                continue
            
            # Check if activity is already downloaded
            activity_start_time = activity.get('startTimeLocal')
            if activity_start_time in downloaded_ids:
                print(f"Activity already downloaded: {activity_name} ({activity_start_time})")
                continue
            
            print(f"Downloading new TCX for activity: {activity_name} (ID: {activity_id})")
            
            try:
                # Download the TCX file
                tcx_data = client.download_activity(activity_id, dl_fmt=client.ActivityDownloadFormat.TCX)
                
                # Handle potential zip file
                if tcx_data.startswith(b'PK'):  # ZIP file signature
                    with tempfile.NamedTemporaryFile() as temp_zip:
                        temp_zip.write(tcx_data)
                        temp_zip.flush()
                        
                        with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
                            tcx_files = [f for f in zip_ref.namelist() if f.endswith('.tcx')]
                            if tcx_files:
                                tcx_content = zip_ref.read(tcx_files[0]).decode('utf-8')
                            else:
                                print(f"No TCX file found in zip for activity {activity_id}")
                                continue
                else:
                    # Direct TCX content
                    tcx_content = tcx_data.decode('utf-8')
                
                # Extract date from TCX content
                activity_date = get_activity_date_from_tcx(tcx_content)
                
                if activity_date:
                    filename = f"{activity_date}.tcx"
                    filepath = os.path.join('raw_tcx', filename)
                    
                    # Check if file already exists (additional safety check)
                    if os.path.exists(filepath):
                        print(f"File {filename} already exists, skipping")
                        continue
                    
                    # Save TCX file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(tcx_content)
                    
                    print(f"Saved: {filename}")
                    new_downloads += 1
                else:
                    # Fallback: use activity ID as filename
                    filename = f"activity_{activity_id}.tcx"
                    filepath = os.path.join('raw_tcx', filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(tcx_content)
                    
                    print(f"Saved: {filename} (using activity ID)")
                    new_downloads += 1
                
            except Exception as e:
                print(f"Error downloading activity {activity_id}: {e}")
                continue
        
        print(f"Download complete! Downloaded {new_downloads} new activities")
        
        # Save the current date as the last download date
        save_last_download_date()
        
    except Exception as e:
        print(f"Error fetching activities: {e}")

def get_last_download_date():
    """Get the last download date from tracking file"""
    try:
        if os.path.exists(LAST_DOWNLOAD_FILE):
            with open(LAST_DOWNLOAD_FILE, 'r') as f:
                date_str = f.read().strip()
                return datetime.strptime(date_str, '%Y-%m-%d')
        else:
            # If no tracking file exists, default to 30 days ago
            return datetime.now() - timedelta(days=30)
    except Exception as e:
        print(f"Error reading last download date: {e}")
        return datetime.now() - timedelta(days=30)

def save_last_download_date():
    """Save today's date as the last download date"""
    try:
        with open(LAST_DOWNLOAD_FILE, 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d'))
    except Exception as e:
        print(f"Error saving last download date: {e}")

def get_downloaded_activity_ids():
    """Get list of already downloaded activity IDs from TCX files"""
    downloaded_ids = set()
    if os.path.exists('raw_tcx'):
        for filename in os.listdir('raw_tcx'):
            if filename.endswith('.tcx'):
                try:
                    filepath = os.path.join('raw_tcx', filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract activity ID from TCX content if it exists
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(content)
                        ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
                        activity_id_elem = root.find('.//tcx:Activity/tcx:Id', ns)
                        if activity_id_elem is not None:
                            downloaded_ids.add(activity_id_elem.text)
                except Exception:
                    # If we can't parse the file, skip it
                    continue
    return downloaded_ids

def main():
    try:
        # Initialize Garmin client
        client = Garmin(email, password)
        client.login()
        print("Successfully logged in to Garmin Connect")
        
        # Download new TCX files since last download
        download_tcx_files(client)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your GARMIN_EMAIL and GARMIN_PASSWORD are set in your .env file")

if __name__ == "__main__":
    main()
