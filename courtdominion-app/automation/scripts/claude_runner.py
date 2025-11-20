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
                "date": None    # None = today
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
    
    # Setup output directory
    today = datetime.date.today().isoformat()
    out_dir = Path('courtdominion-automation/outputs/generated') / today
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"CLAUDE RUNNER - {today}")
    print(f"{'='*60}\n")
    
    # Get projections
    projections = get_projections()
    
    if projections and projections.get('status') == 'success':
        proj_file = out_dir / 'projections.json'
        with open(proj_file, 'w') as f:
            json.dump(projections, f, indent=2)
        print(f"\n✅ Projections saved: {proj_file}")
        print(f"   Status: {projections.get('status')}")
    else:
        print("\n❌ Failed to get projections")
        # Create empty file so pipeline doesn't break
        with open(out_dir / 'projections.json', 'w') as f:
            json.dump({'generated_at': datetime.datetime.utcnow().isoformat(), 'status': 'error', 'error': 'Failed to fetch'}, f)
    
    # Get injuries
    injuries = get_injury_feed()
    with open(out_dir / 'injury_feed.json', 'w') as f:
        json.dump(injuries, f, indent=2)
    print(f"✅ Injury feed saved")
    
    print(f"\n{'='*60}")
    print("CLAUDE RUNNER COMPLETE")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
