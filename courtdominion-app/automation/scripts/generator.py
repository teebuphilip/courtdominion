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
    
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set")
        return None
    
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
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"OpenAI API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR calling OpenAI: {e}")
        return None


def generate_narrative(projections):
    """Generate narrative based on projections"""
    
    if not projections or projections.get('status') != 'success':
        return "Daily fantasy basketball update with projections and waiver wire analysis."
    
    # Get preview data from backend response
    preview = projections.get('preview', {})
    
    # Try to extract meaningful data from preview
    # The format will depend on what the legacy dbb2_main.py outputs
    if preview:
        preview_str = json.dumps(preview, indent=2)[:500]  # First 500 chars
        
        prompt = f"""Based on these NBA projection results, write a compelling narrative for fantasy basketball managers:

{preview_str}

Create a 2-3 sentence hook about today's fantasy basketball opportunities. Focus on:
- Waiver wire pickups
- Streaming candidates  
- Injury impacts
- Schedule advantages

Keep it urgent, actionable, and under 100 words."""
        
        narrative = call_openai(prompt, max_tokens=150)
        
        if narrative:
            return narrative.strip()
    
    # Fallback
    return "Today's projections reveal key waiver wire opportunities and streaming candidates for your fantasy lineup."


def generate_platform_content(platform, narrative, projections):
    """Generate platform-specific content"""
    
    today = datetime.date.today().strftime("%B %d, %Y")
    
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
    
    content = call_openai(prompt, max_tokens=600)
    
    if content:
        return content.strip()
    else:
        return f"{platform.upper()} POST ({today})\n\n{narrative}\n\nKey Takeaways:\n- Check waiver wire\n- Monitor injury reports\n- Optimize your lineup\n\n[Generated content failed - using fallback]"


def main():
    """Main generator"""
    
    today = datetime.date.today().isoformat()
    out_dir = Path('courtdominion-automation/outputs/generated') / today
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"CONTENT GENERATOR - {today}")
    print(f"{'='*60}\n")
    
    # Read projections
    proj_file = out_dir / 'projections.json'
    projections = None
    if proj_file.exists():
        with open(proj_file) as f:
            projections = json.load(f)
        status = projections.get('status', 'unknown')
        print(f"✓ Loaded projections (status: {status})")
    else:
        print("⚠ No projections found, using fallback")
    
    # Generate narrative
    print("\nGenerating narrative with OpenAI...")
    narrative = generate_narrative(projections)
    print(f"✓ Narrative: {narrative[:100]}...")
    
    # Generate platform content
    platforms = ['twitter', 'reddit', 'discord', 'linkedin', 'email']
    generated = {}
    
    for platform in platforms:
        print(f"\nGenerating {platform} content...")
        content = generate_platform_content(platform, narrative, projections)
        
        if content:
            fname = out_dir / f"{platform}_draft.txt"
            with open(fname, 'w') as f:
                f.write(content)
            generated[platform] = str(fname)
            print(f"✓ {platform}: {len(content)} chars")
        else:
            print(f"✗ {platform}: Failed")
    
    # Write rationale
    rationale = {
        'date': today,
        'narrative': narrative,
        'why': 'Data-driven insights from real projections to maximize engagement and provide actionable advice',
        'choices': ['Waiver wire urgency', 'Schedule advantages', 'Injury impacts'],
        'model_used': OPENAI_MODEL
    }
    
    with open(out_dir / 'rationale.json', 'w') as f:
        json.dump(rationale, f, indent=2)
    print(f"\n✓ Rationale saved")
    
    # Write manifest
    manifest = {
        'date': today,
        'generated': generated,
        'narrative': narrative,
        'platforms_count': len(generated)
    }
    
    with open(out_dir / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"✓ Manifest saved")
    
    print(f"\n{'='*60}")
    print(f"CONTENT GENERATION COMPLETE")
    print(f"Generated content for {len(generated)}/{len(platforms)} platforms")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
