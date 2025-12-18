"""
Claude Runner - Calls CourtDominion Backend API for real projections
"""
import json
import datetime
import os
import requests
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
API_KEY = os.getenv('COURTDOMINION_API_KEY', '')

def get_projections():
    """Get projections from backend API"""
    
    print("Fetching projections from backend...")
    
    try:
        # Call the backend's run_projections endpoint
        response = requests.post(
            f"{BACKEND_URL}/v1/run_projections",
            json={
                "players": [],  # Empty = all players
# original line
#                "date": None    # None = today

                "date": datetime.date.today().isoformat()
            },
            timeout=120  # Projections can take time
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Got projections successfully")
            print(f"  Status: {result.get('status')}")
            print(f"  Output: {result.get('output_file')}")
            
            # The backend returns preview of the data
            preview = result.get('preview', {})
            
            return {
                'generated_at': datetime.datetime.utcnow().isoformat(),
                'backend_response': result,
                'preview': preview,
                'status': 'success'
            }
        else:
            print(f"⚠ Backend returned HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR calling backend: {e}")
        return None


def get_injury_feed():
    """Get injury updates (placeholder - implement when backend has injury endpoint)"""
    
    # TODO: Call backend injury endpoint when available
    # For now, return empty
    return {
        'generated_at': datetime.datetime.utcnow().isoformat(),
        'injuries': []
    }


def main():
    """Main runner"""
    
    # Setup output directory - MUST MATCH shell script BASE_DIR
    today = datetime.date.today().isoformat()
    out_dir = Path('automation/outputs/generated') / today
    
    print(f"\n{'='*60}")
    print(f"CLAUDE RUNNER - {today}")
    print(f"{'='*60}\n")
    
    # DEBUG: Show where we're trying to save files
    print(f"DEBUG: Current working directory: {os.getcwd()}")
    print(f"DEBUG: Output directory: {out_dir}")
    print(f"DEBUG: Absolute output path: {out_dir.resolve()}")
    
    # Create the directory
    print(f"DEBUG: Creating directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"DEBUG: Directory exists: {out_dir.exists()}")
    print()
    
    # Get projections
    projections = get_projections()
    
    if projections and projections.get('status') == 'success':
        proj_file = out_dir / 'projections.json'
        
        # DEBUG: Show file operation
        print(f"DEBUG: Saving projections to: {proj_file}")
        print(f"DEBUG: Absolute path: {proj_file.resolve()}")
        
        with open(proj_file, 'w') as f:
            json.dump(projections, f, indent=2)
        
        # DEBUG: Verify file was created
        print(f"DEBUG: File exists after write: {proj_file.exists()}")
        if proj_file.exists():
            print(f"DEBUG: File size: {proj_file.stat().st_size} bytes")
        
        print(f"\n✅ Projections saved: {proj_file}")
        print(f"   Status: {projections.get('status')}")
    else:
        print("\n❌ Failed to get projections")
        # Create empty file so pipeline doesn't break
        empty_file = out_dir / 'projections.json'
        print(f"DEBUG: Creating empty projections file: {empty_file}")
        with open(empty_file, 'w') as f:
            json.dump({'generated_at': datetime.datetime.utcnow().isoformat(), 'status': 'error', 'error': 'Failed to fetch'}, f)
    
    # Get injuries
    injuries = get_injury_feed()
    injury_file = out_dir / 'injury_feed.json'
    
    # DEBUG: Show file operation
    print(f"DEBUG: Saving injury feed to: {injury_file}")
    print(f"DEBUG: Absolute path: {injury_file.resolve()}")
    
    with open(injury_file, 'w') as f:
        json.dump(injuries, f, indent=2)
    
    # DEBUG: Verify file was created
    print(f"DEBUG: File exists after write: {injury_file.exists()}")
    if injury_file.exists():
        print(f"DEBUG: File size: {injury_file.stat().st_size} bytes")
    
    print(f"✅ Injury feed saved")
    
    print(f"\n{'='*60}")
    print("CLAUDE RUNNER COMPLETE")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
