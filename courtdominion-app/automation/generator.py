"""
Content Generator - Uses OpenAI API to generate real marketing content

Generates platform-specific content (Twitter, Reddit, Discord, LinkedIn, Email)
from NBA projections using ChatGPT/OpenAI API.

UPDATED: Now filters out superstars (Jokic, Giannis, etc.) to focus on
deep sleepers, waiver wire targets, and streaming candidates.
"""
import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import requests


# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')


def load_blacklist() -> Set[str]:
    """
    Load superstar blacklist - players to exclude from content.
    
    Reads from superstar_blacklist.txt in same directory.
    Players in this list are obvious/boring picks that everyone knows.
    Content should focus on deep sleepers and waiver wire targets instead.
    
    Returns:
        Set of player names (lowercase for case-insensitive matching)
    """
    blacklist_file = Path(__file__).parent / 'superstar_blacklist.txt'
    
    if not blacklist_file.exists():
        print("⚠️  Blacklist file not found, using empty blacklist")
        return set()
    
    blacklist = set()
    try:
        with open(blacklist_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    blacklist.add(line.lower())
        
        print(f"✓ Loaded blacklist: {len(blacklist)} superstars excluded from content")
        return blacklist
        
    except Exception as e:
        print(f"⚠️  Error loading blacklist: {e}")
        return set()


def call_openai(prompt: str, max_tokens: int = 500) -> Optional[str]:
    """
    Call OpenAI API to generate content.
    
    Args:
        prompt: The prompt to send to OpenAI
        max_tokens: Maximum tokens in response
        
    Returns:
        Generated text or None if failed
    """
    if not OPENAI_API_KEY:
        print("  ERROR: OPENAI_API_KEY not set in environment")
        print("  Set it with: export OPENAI_API_KEY='your-key-here'")
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
                    {
                        'role': 'system',
                        'content': 'You are a fantasy basketball expert who writes engaging, actionable content for fantasy managers. Focus on DEEP SLEEPERS, waiver wire targets, and streaming candidates - NOT obvious superstars everyone already knows about.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': max_tokens,
                'temperature': 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()['choices'][0]['message']['content']
            return result
        else:
            print(f"  ERROR: OpenAI API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"  ERROR calling OpenAI: {e}")
        return None


def generate_narrative(projections: List[Dict], insights: List[Dict]) -> str:
    """
    Generate narrative summary from projections and insights.
    
    FILTERS OUT SUPERSTARS - focuses on deep sleepers and waiver wire targets.
    
    Args:
        projections: List of player projections
        insights: List of generated insights
        
    Returns:
        Narrative summary text
    """
    if not projections or not insights:
        return "Daily fantasy basketball update with projections and waiver wire analysis."
    
    # Load blacklist of superstars to exclude
    blacklist = load_blacklist()
    
    # Filter projections to exclude blacklisted players
    filtered_projections = [
        p for p in projections 
        if p.get('name', '').lower() not in blacklist
    ]
    
    excluded_count = len(projections) - len(filtered_projections)
    if excluded_count > 0:
        print(f"✓ Filtered out {excluded_count} superstars, focusing on {len(filtered_projections)} deep sleepers/waiver targets")
    
    # Get top performers by fantasy points (from FILTERED list)
    top_performers = sorted(
        filtered_projections, 
        key=lambda x: x.get('fantasy_points', 0), 
        reverse=True
    )[:5]
    
    # Get top value plays (high fantasy points, low consistency)
    value_plays = sorted(
        filtered_projections, 
        key=lambda x: (x.get('fantasy_points', 0) / max(x.get('consistency', 1), 1)), 
        reverse=True
    )[:3]
    
    # Build context for OpenAI
    context = {
        'top_performers': [{'name': p['name'], 'fantasy_points': p.get('fantasy_points', 0)} for p in top_performers],
        'value_plays': [{'name': p['name'], 'upside': p.get('ceiling', 0)} for p in value_plays],
        'total_players': len(filtered_projections)
    }
    
    prompt = f"""Based on these NBA fantasy basketball projections, write a compelling 2-3 sentence narrative:

Top Performers (DEEP SLEEPERS):
{', '.join([f"{p['name']} ({p['fantasy_points']:.1f} FP)" for p in top_performers])}

Value Plays (High Upside):
{', '.join([f"{p['name']} ({p.get('ceiling', 0):.1f} ceiling)" for p in value_plays])}

Create an urgent, actionable hook about today's fantasy opportunities. Focus on:
- Waiver wire targets (NOT superstars)
- Streaming candidates
- Deep sleepers and value plays
- Players most fantasy managers are overlooking

Keep it under 100 words, exciting, and actionable. DO NOT mention obvious superstars."""
    
    narrative = call_openai(prompt, max_tokens=150)
    
    if narrative:
        return narrative.strip()
    
    # Fallback narrative (using filtered list)
    if top_performers:
        top_3_names = ', '.join([p['name'] for p in top_performers[:3]])
        return f"Today's projections highlight strong waiver wire opportunities from {top_3_names}. Key streaming candidates and deep sleepers identified for savvy fantasy managers."
    else:
        return "Daily fantasy basketball update with waiver wire analysis and streaming candidates."


def generate_platform_content(platform: str, narrative: str, projections: List[Dict], insights: List[Dict]) -> str:
    """
    Generate platform-specific content.
    
    FILTERS OUT SUPERSTARS - focuses on actionable waiver wire advice.
    
    Args:
        platform: Platform name (twitter, reddit, discord, linkedin, email)
        narrative: Overall narrative summary
        projections: Player projections
        insights: Generated insights
        
    Returns:
        Platform-specific content
    """
    today = datetime.date.today().strftime("%B %d, %Y")
    
    # Load blacklist and filter projections
    blacklist = load_blacklist()
    filtered_projections = [
        p for p in projections 
        if p.get('name', '').lower() not in blacklist
    ]
    
    # Get some specific data for prompts (from FILTERED list)
    top_5 = sorted(filtered_projections, key=lambda x: x.get('fantasy_points', 0), reverse=True)[:5]
    top_names = [p['name'] for p in top_5]
    
    # Platform-specific prompts
    prompts = {
        'twitter': f"""Write a Twitter thread (3-4 tweets, 280 chars each) about today's fantasy basketball waiver wire opportunities.

Context: {narrative}

Deep Sleepers Today: {', '.join(top_names[:3])}

Make it:
- Engaging with emojis
- Include #FantasyBasketball #NBA hashtags
- Focus on WAIVER WIRE and STREAMING picks (NOT obvious superstars)
- Actionable advice for savvy managers
- Thread format (1/, 2/, 3/)

Output each tweet on a new line starting with the number.""",

        'reddit': f"""Write a Reddit post for r/fantasybball about today's waiver wire and streaming opportunities.

Context: {narrative}

Deep Sleepers: {', '.join(top_names)}

Include:
- Engaging title
- 3-4 key player recommendations with brief analysis
- WHY these are waiver wire/streaming targets
- Schedule advantages
- Ownership percentages likely low

Focus on players most fantasy managers are overlooking, NOT obvious superstars.

Format: Reddit markdown style, ~300 words.""",

        'discord': f"""Write a Discord message for a fantasy basketball community about today's waiver wire opportunities.

Context: {narrative}

Waiver Targets: {', '.join(top_names[:3])}

Make it:
- Casual, community-focused tone
- Use Discord formatting (bold, italics)
- Include 3 specific waiver wire recommendations
- Focus on streaming and deep sleepers
- Quick-hitting analysis
- ~200 words

Do NOT mention obvious superstars. Focus on actionable picks.""",

        'linkedin': f"""Write a professional LinkedIn post about fantasy basketball analytics and today's waiver wire insights.

Context: {narrative}

Make it:
- Professional but approachable
- Focus on data-driven waiver wire decisions
- Business-casual tone
- Mention these are undervalued opportunities
- ~250 words
- Include relevant hashtags""",

        'email': f"""Write an email newsletter for fantasy basketball subscribers.

Subject: Daily Waiver Wire Insights - {today}

Context: {narrative}

Deep Sleepers: {', '.join(top_names)}

Include:
- Engaging opening
- 3 key waiver wire opportunities today
- Why these players are undervalued
- Quick streaming notes
- Call to action
- ~300 words

Focus on actionable advice for savvy managers, NOT obvious picks."""
    }
    
    prompt = prompts.get(platform, prompts['twitter'])
    content = call_openai(prompt, max_tokens=600)
    
    if content:
        return content.strip()
    
    # Fallback content (using filtered list)
    return f"""{platform.upper()} POST ({today})

{narrative}

Top Waiver Wire Targets Today:
{chr(10).join([f'- {p["name"]}: {p.get("fantasy_points", 0):.1f} fantasy points' for p in top_5[:3]])}

Key Takeaways:
- Undervalued streaming candidates identified
- Deep sleepers for savvy managers
- Monitor injury reports for opportunities

#FantasyBasketball #NBA #WaiverWire

[Generated by CourtDominion - Real NBA Projections]"""


def generate_all_content(
    data_dir: Path,
    projections: List[Dict],
    insights: List[Dict],
    risk_metrics: List[Dict]
) -> Optional[Path]:
    """
    Generate all platform content.
    
    Args:
        data_dir: Base data directory
        projections: Player projections
        insights: Generated insights
        risk_metrics: Risk assessments
        
    Returns:
        Path to generated content directory, or None if failed
    """
    today = datetime.date.today().isoformat()
    out_dir = Path(data_dir) / 'generated' / today
    
    print(f"\n{'='*70}")
    print(f"  CONTENT GENERATOR - {today}")
    print(f"{'='*70}\n")
    
    print(f"Output directory: {out_dir}")
    print(f"Projections: {len(projections)} players")
    print(f"Insights: {len(insights)} items")
    print()
    
    # Create directory
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Check OpenAI API key
    if not OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not set!")
        print("⚠️  Content generation will use fallback templates")
        print("⚠️  Set environment variable: export OPENAI_API_KEY='your-key'")
        print()
    else:
        print(f"✓ OpenAI API key configured")
        print(f"✓ Using model: {OPENAI_MODEL}")
        print()
    
    # Generate narrative
    print("Generating narrative summary...")
    narrative = generate_narrative(projections, insights)
    print(f"✓ Narrative: {narrative[:100]}...")
    print()
    
    # Generate platform content
    platforms = ['twitter', 'reddit', 'discord', 'linkedin', 'email']
    generated = {}
    
    for platform in platforms:
        print(f"Generating {platform} content...")
        
        content = generate_platform_content(platform, narrative, projections, insights)
        
        if content:
            fname = out_dir / f"{platform}_draft.txt"
            
            with open(fname, 'w') as f:
                f.write(content)
            
            generated[platform] = str(fname)
            print(f"✓ {platform}: {len(content)} chars → {fname.name}")
        else:
            print(f"✗ {platform}: Failed")
    
    # Write rationale
    rationale = {
        'date': today,
        'narrative': narrative,
        'why': 'Data-driven insights from real NBA projections focusing on waiver wire and streaming opportunities',
        'choices': ['Waiver wire urgency', 'Deep sleepers', 'Streaming candidates'],
        'model_used': OPENAI_MODEL,
        'projections_count': len(projections),
        'superstar_filtering': 'Enabled - focuses on actionable picks'
    }
    
    with open(out_dir / 'rationale.json', 'w') as f:
        json.dump(rationale, f, indent=2)
    
    print(f"✓ Rationale saved")
    
    # Write manifest
    manifest = {
        'date': today,
        'generated': generated,
        'narrative': narrative,
        'platforms_count': len(generated),
        'projections_count': len(projections)
    }
    
    with open(out_dir / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✓ Manifest saved")
    
    print(f"\n{'='*70}")
    print(f"CONTENT GENERATION COMPLETE")
    print(f"Generated: {len(generated)}/{len(platforms)} platforms")
    print(f"Location: {out_dir}")
    print(f"{'='*70}\n")
    
    return out_dir if generated else None


# For standalone testing
if __name__ == '__main__':
    # Test with mock data
    print("Testing content generator with mock data...")
    
    mock_projections = [
        {'name': 'LeBron James', 'fantasy_points': 45.2, 'consistency': 85, 'ceiling': 55.0},
        {'name': 'Luka Doncic', 'fantasy_points': 48.1, 'consistency': 90, 'ceiling': 60.0},
        {'name': 'Anthony Davis', 'fantasy_points': 42.3, 'consistency': 75, 'ceiling': 52.0},
    ]
    
    mock_insights = [
        {'player_id': '2544', 'value_score': 8.5},
        {'player_id': '1629029', 'value_score': 9.2},
    ]
    
    output_dir = generate_all_content(
        data_dir=Path('/data/outputs'),
        projections=mock_projections,
        insights=mock_insights,
        risk_metrics=[]
    )
    
    if output_dir:
        print(f"\n✓ Test successful! Content at: {output_dir}")
    else:
        print(f"\n✗ Test failed")
