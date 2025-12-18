"""
Content Generator - Uses OpenAI API to generate real marketing content
"""
import os
import json
import datetime
from pathlib import Path
import requests

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')

def call_openai(prompt, max_tokens=500):
    """Call OpenAI API"""
    
    print(f"  DEBUG: call_openai() started")
    print(f"  DEBUG: Max tokens: {max_tokens}")
    print(f"  DEBUG: Prompt length: {len(prompt)} chars")
    print(f"  DEBUG: First 100 chars of prompt: {prompt[:100]}...")
    
    if not OPENAI_API_KEY:
        print("  ERROR: OPENAI_API_KEY not set")
        return None
    
    print(f"  DEBUG: API key is set (length: {len(OPENAI_API_KEY)})")
    print(f"  DEBUG: Model: {OPENAI_MODEL}")
    print(f"  DEBUG: Making API request to OpenAI...")
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': OPENAI_MODEL,
                'messages': [
                    {'role': 'system', 'content': 'You are a fantasy basketball expert who writes engaging, actionable content for fantasy managers.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': max_tokens,
                'temperature': 0.7
            },
            timeout=30
        )
        
        print(f"  DEBUG: API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()['choices'][0]['message']['content']
            print(f"  DEBUG: API call successful")
            print(f"  DEBUG: Response length: {len(result)} chars")
            print(f"  DEBUG: First 100 chars: {result[:100]}...")
            return result
        else:
            print(f"  ERROR: OpenAI API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"  ERROR calling OpenAI: {e}")
        print(f"  DEBUG: Exception type: {type(e).__name__}")
        return None


def generate_narrative(projections):
    """Generate narrative based on projections"""
    
    print(f"\nDEBUG: generate_narrative() started")
    print(f"DEBUG: Projections is None: {projections is None}")
    
    if not projections or projections.get('status') != 'success':
        print(f"DEBUG: No valid projections, using fallback narrative")
        return "Daily fantasy basketball update with projections and waiver wire analysis."
    
    # Get preview data from backend response
    preview = projections.get('preview', {})
    print(f"DEBUG: Preview data exists: {bool(preview)}")
    
    # Try to extract meaningful data from preview
    # The format will depend on what the legacy dbb2_main.py outputs
    if preview:
        preview_str = json.dumps(preview, indent=2)[:500]  # First 500 chars
        print(f"DEBUG: Preview string length: {len(preview_str)} chars")
        print(f"DEBUG: Building prompt for OpenAI...")
        
        prompt = f"""Based on these NBA projection results, write a compelling narrative for fantasy basketball managers:

{preview_str}

Create a 2-3 sentence hook about today's fantasy basketball opportunities. Focus on:
- Waiver wire pickups
- Streaming candidates  
- Injury impacts
- Schedule advantages

Keep it urgent, actionable, and under 100 words."""
        
        print(f"DEBUG: Calling OpenAI for narrative...")
        narrative = call_openai(prompt, max_tokens=150)
        
        if narrative:
            print(f"DEBUG: Narrative generated successfully")
            print(f"DEBUG: Narrative length: {len(narrative)} chars")
            return narrative.strip()
        else:
            print(f"DEBUG: OpenAI call failed, using fallback")
    
    # Fallback
    print(f"DEBUG: Using fallback narrative")
    return "Today's projections reveal key waiver wire opportunities and streaming candidates for your fantasy lineup."


def generate_platform_content(platform, narrative, projections):
    """Generate platform-specific content"""
    
    print(f"  DEBUG: generate_platform_content() for {platform}")
    print(f"  DEBUG: Narrative length: {len(narrative)} chars")
    print(f"  DEBUG: Projections exists: {projections is not None}")
    
    today = datetime.date.today().strftime("%B %d, %Y")
    print(f"  DEBUG: Date: {today}")
    
    # Platform-specific prompts
    prompts = {
        'twitter': f"""Write a Twitter thread (3-4 tweets, 280 chars each) about today's fantasy basketball opportunities.

Context: {narrative}

Make it:
- Engaging with emojis
- Include #FantasyBasketball #NBA hashtags
- Actionable advice
- Thread format (1/, 2/, 3/)

Output each tweet on a new line starting with the number.""",

        'reddit': f"""Write a Reddit post for r/fantasybball about today's waiver wire and streaming opportunities.

Context: {narrative}

Include:
- Engaging title
- 3-4 key player recommendations with brief analysis
- Schedule advantages this week
- Injury updates impact

Format: Reddit markdown style, ~300 words.""",

        'discord': f"""Write a Discord message for a fantasy basketball community about today's opportunities.

Context: {narrative}

Make it:
- Casual, community-focused tone
- Use Discord formatting (bold, italics)
- Include 3 specific recommendations
- Quick-hitting analysis
- ~200 words""",

        'linkedin': f"""Write a professional LinkedIn post about fantasy basketball analytics and today's insights.

Context: {narrative}

Make it:
- Professional but approachable
- Focus on data-driven decisions
- Business-casual tone
- ~250 words
- Include relevant hashtags""",

        'email': f"""Write an email newsletter for fantasy basketball subscribers.

Subject: Daily Fantasy Insights - {today}

Context: {narrative}

Include:
- Engaging opening
- 3 key opportunities today
- Quick injury notes
- Call to action
- ~300 words"""
    }
    
    prompt = prompts.get(platform, prompts['twitter'])
    print(f"  DEBUG: Using prompt for {platform}")
    print(f"  DEBUG: Prompt length: {len(prompt)} chars")
    print(f"  DEBUG: Calling OpenAI for {platform} content...")
    
    content = call_openai(prompt, max_tokens=600)
    
    print(f"  DEBUG: OpenAI call completed for {platform}")
    print(f"  DEBUG: Content received: {content is not None}")
    
    if content:
        print(f"  DEBUG: Content length: {len(content)} chars")
        print(f"  DEBUG: Returning stripped content")
        return content.strip()
    else:
        print(f"  DEBUG: No content received, using fallback")
        fallback = f"{platform.upper()} POST ({today})\n\n{narrative}\n\nKey Takeaways:\n- Check waiver wire\n- Monitor injury reports\n- Optimize your lineup\n\n[Generated content failed - using fallback]"
        print(f"  DEBUG: Fallback length: {len(fallback)} chars")
        return fallback


def main():
    """Main generator"""
    
    # MUST MATCH shell script BASE_DIR
    today = datetime.date.today().isoformat()
    out_dir = Path('automation/outputs/generated') / today
    
    print(f"\n{'='*60}")
    print(f"CONTENT GENERATOR - {today}")
    print(f"{'='*60}\n")
    
    # DEBUG: Show paths
    print(f"DEBUG: Current working directory: {os.getcwd()}")
    print(f"DEBUG: Output directory: {out_dir}")
    print(f"DEBUG: Absolute output path: {out_dir.resolve()}")
    
    # Create directory if needed
    print(f"DEBUG: Creating directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"DEBUG: Directory exists: {out_dir.exists()}")
    print()
    
    # Read projections
    proj_file = out_dir / 'projections.json'
    projections = None
    
    # DEBUG: Check if projections file exists
    print(f"DEBUG: Looking for projections at: {proj_file}")
    print(f"DEBUG: Absolute path: {proj_file.resolve()}")
    print(f"DEBUG: File exists: {proj_file.exists()}")
    
    if proj_file.exists():
        print(f"DEBUG: File size: {proj_file.stat().st_size} bytes")
        print(f"DEBUG: Reading projections file...")
        
        with open(proj_file) as f:
            projections = json.load(f)
        
        status = projections.get('status', 'unknown')
        print(f"✓ Loaded projections (status: {status})")
    else:
        print(f"⚠ No projections found at {proj_file}")
        print("⚠ Using fallback content")
    
    # Generate narrative
    print("\nGenerating narrative with OpenAI...")
    narrative = generate_narrative(projections)
    print(f"✓ Narrative: {narrative[:100]}...")
    
    # Generate platform content
    platforms = ['twitter', 'reddit', 'discord', 'linkedin', 'email']
    generated = {}
    
    # Log directory for platform logs
    logs_dir = Path('automation/outputs/logs')
    
    print(f"DEBUG: Platform logs directory: {logs_dir}")
    print(f"DEBUG: Creating logs directory if needed...")
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"DEBUG: Logs directory exists: {logs_dir.exists()}")
    print()
    
    for platform in platforms:
        print(f"\n{'='*60}")
        print(f"Generating {platform} content...")
        print(f"{'='*60}")
        print(f"DEBUG: Platform: {platform}")
        print(f"DEBUG: Starting content generation...")
        
        content = generate_platform_content(platform, narrative, projections)
        
        print(f"DEBUG: Content generation completed")
        print(f"DEBUG: Content is None: {content is None}")
        
        if content:
            fname = out_dir / f"{platform}_draft.txt"
            
            # DEBUG: Show file operation
            print(f"DEBUG: Saving {platform} content to: {fname}")
            print(f"DEBUG: Absolute path: {fname.resolve()}")
            print(f"DEBUG: Content length: {len(content)} chars")
            print(f"DEBUG: First 100 chars: {content[:100]}...")
            
            with open(fname, 'w') as f:
                f.write(content)
            
            # DEBUG: Verify file was created
            print(f"DEBUG: File exists after write: {fname.exists()}")
            if fname.exists():
                print(f"DEBUG: File size: {fname.stat().st_size} bytes")
            
            generated[platform] = str(fname)
            print(f"✓ {platform}: {len(content)} chars")
            
            # APPEND to platform log file
            # Format: DATE - TIME - POST HEADLINE - PUBLISHED/NOTPUBLISHED
            log_file = logs_dir / f"{platform}.log"
            
            # Get current date and time separately
            now = datetime.datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H:%M:%S')
            
            # Extract a headline from the content (first 50 chars)
            headline = content.split('\n')[0][:50].strip()
            if not headline:
                headline = f"{platform} content"
            
            # Format: DATE - TIME - POST HEADLINE - NOT PUBLISHED
            log_line = f"{date_str} - {time_str} - {headline} - NOT PUBLISHED\n"
            
            print(f"DEBUG: Appending to log: {log_file}")
            print(f"DEBUG: Log line: {log_line.strip()}")
            
            # Create or append to log file
            with open(log_file, 'a') as f:
                f.write(log_line)
            
            print(f"DEBUG: Log file updated: {log_file.exists()}")
            print(f"✓ Logged to {platform}.log")
            
        else:
            print(f"DEBUG: Content generation failed - content is None")
            print(f"✗ {platform}: Failed (no content generated)")
    
    # Write rationale
    rationale = {
        'date': today,
        'narrative': narrative,
        'why': 'Data-driven insights from real projections to maximize engagement and provide actionable advice',
        'choices': ['Waiver wire urgency', 'Schedule advantages', 'Injury impacts'],
        'model_used': OPENAI_MODEL
    }
    
    rationale_file = out_dir / 'rationale.json'
    print(f"\nDEBUG: Saving rationale to: {rationale_file}")
    
    with open(rationale_file, 'w') as f:
        json.dump(rationale, f, indent=2)
    
    print(f"DEBUG: File exists: {rationale_file.exists()}")
    print(f"✓ Rationale saved")
    
    # Write manifest
    manifest = {
        'date': today,
        'generated': generated,
        'narrative': narrative,
        'platforms_count': len(generated)
    }
    
    manifest_file = out_dir / 'manifest.json'
    print(f"DEBUG: Saving manifest to: {manifest_file}")
    
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"DEBUG: File exists: {manifest_file.exists()}")
    print(f"✓ Manifest saved")
    
    print(f"\n{'='*60}")
    print(f"CONTENT GENERATION COMPLETE")
    print(f"Generated content for {len(generated)}/{len(platforms)} platforms")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
