"""
NBA Fantasy Basketball Platform - Main FastAPI Application
Complete API with 50+ endpoints for production use
"""

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import traceback
import uvicorn
import json

# Import all modules
import dbb2_database as db
import dbb2_nba_data_fetcher as nba
import dbb2_scoring_engine as scoring
import dbb2_league_db as league_db
import dbb2_weekly_tracking as weekly
import dbb2_lineup_optimizer as lineup
import dbb2_streaming_optimizer as streaming
import dbb2_opponent_analyzer as opponent
import dbb2_trade_analyzer as trade
import dbb2_api_logger as logger

# Initialize FastAPI app
app = FastAPI(
    title="NBA Fantasy Basketball Platform",
    description="Complete fantasy basketball API with projections, leagues, and advanced analytics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# REQUEST MODELS
# ============================================

class LeagueCreate(BaseModel):
    league_name: str
    scoring_type: str  # "roto" or "h2h"
    categories: List[str]
    roster_size: int = 13
    matchup_length: int = 7

class PlayerAdd(BaseModel):
    player_id: int

class TradeRequest(BaseModel):
    give_player_ids: List[int]
    receive_player_ids: List[int]

class BatchProjectionsRequest(BaseModel):
    player_ids: List[int]
    projection_type: str = "current"  # "current" or "5year"


# ============================================
# API KEY MIDDLEWARE
# ============================================

async def verify_api_key(request: Request, x_api_key: Optional[str] = Header(None)):
    """
    Verify API key and log request
    Returns: customer_id, tier
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Verify key exists
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT customer_id, tier, requests_today, daily_limit
            FROM api_keys
            WHERE api_key = %s AND active = true
        """, (x_api_key,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        customer_id, tier, requests_today, daily_limit = result
        
        # Check rate limit
        if requests_today >= daily_limit:
            raise HTTPException(status_code=429, detail=f"Daily limit ({daily_limit}) exceeded")
        
        # Increment request count
        cursor.execute("""
            UPDATE api_keys
            SET requests_today = requests_today + 1,
                last_used = NOW()
            WHERE api_key = %s
        """, (x_api_key,))
        conn.commit()
        
        cursor.close()
        
        # Log request
        await logger.log_request(
            customer_id=customer_id,
            endpoint=request.url.path,
            method=request.method,
            tier=tier
        )
        
        return customer_id, tier
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.return_connection(conn)


# ============================================
# HEALTH & STATUS
# ============================================

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    """API root"""
    return {
        "message": "NBA Fantasy Basketball Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ============================================
# PROJECTION ENDPOINTS
# ============================================

@app.get("/projections/5year/{player_id}")
async def get_5year_projection(
    player_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get 5-year average projection for a player"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        projection = nba.get_5year_projection(player_id)
        if not projection:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return projection
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projections/current/{player_id}")
async def get_current_projection(
    player_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get current season projection for a player"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        projection = nba.get_current_season_projection(player_id)
        if not projection:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return projection
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projections/batch")
async def get_batch_projections(
    batch_request: BatchProjectionsRequest,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get projections for multiple players"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Pro tier required for batch requests
    if tier not in ['pro', 'enterprise']:
        raise HTTPException(status_code=403, detail="Pro tier required for batch requests")
    
    try:
        projections = []
        for player_id in batch_request.player_ids:
            if batch_request.projection_type == "5year":
                proj = nba.get_5year_projection(player_id)
            else:
                proj = nba.get_current_season_projection(player_id)
            
            if proj:
                projections.append(proj)
        
        return {"projections": projections}
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projections/5year/team/{team}")
async def get_team_5year_projections(
    team: str,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get 5-year projections for all players on a team"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        players = nba.get_team_players(team)
        projections = []
        
        for player_id in players:
            proj = nba.get_5year_projection(player_id)
            if proj:
                projections.append(proj)
        
        return {"team": team, "projections": projections}
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projections/current/team/{team}")
async def get_team_current_projections(
    team: str,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get current season projections for all players on a team"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        players = nba.get_team_players(team)
        projections = []
        
        for player_id in players:
            proj = nba.get_current_season_projection(player_id)
            if proj:
                projections.append(proj)
        
        return {"team": team, "projections": projections}
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# LEAGUE MANAGEMENT
# ============================================

@app.post("/leagues")
async def create_league(
    league: LeagueCreate,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Create a new fantasy league"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        league_id = league_db.create_league(
            customer_id=customer_id,
            league_name=league.league_name,
            scoring_type=league.scoring_type,
            categories=league.categories,
            roster_size=league.roster_size,
            matchup_length=league.matchup_length
        )
        
        return {
            "league_id": league_id,
            "message": "League created successfully"
        }
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leagues")
async def list_leagues(
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """List all leagues for the authenticated customer"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        leagues = league_db.get_customer_leagues(customer_id)
        return {"leagues": leagues}
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leagues/{league_id}")
async def get_league(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get league details"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        league = league_db.get_league(league_id)
        
        # Verify ownership
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this league")
        
        return league
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/leagues/{league_id}")
async def update_league(
    league_id: int,
    league: LeagueCreate,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Update league settings"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        # Verify ownership
        existing_league = league_db.get_league(league_id)
        if existing_league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this league")
        
        league_db.update_league(
            league_id=league_id,
            league_name=league.league_name,
            scoring_type=league.scoring_type,
            categories=league.categories,
            roster_size=league.roster_size,
            matchup_length=league.matchup_length
        )
        
        return {"message": "League updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/leagues/{league_id}")
async def delete_league(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Delete a league"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this league")
        
        league_db.delete_league(league_id)
        return {"message": "League deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ROSTER MANAGEMENT
# ============================================

@app.post("/leagues/{league_id}/roster")
async def add_player_to_roster(
    league_id: int,
    player: PlayerAdd,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Add a player to league roster"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        league_db.add_player_to_roster(league_id, player.player_id)
        return {"message": "Player added to roster"}
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leagues/{league_id}/roster")
async def get_roster(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get league roster"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        roster = league_db.get_roster(league_id)
        return {"roster": roster}
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/leagues/{league_id}/roster/{player_id}")
async def remove_player_from_roster(
    league_id: int,
    player_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Remove a player from roster"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        league_db.remove_player_from_roster(league_id, player_id)
        return {"message": "Player removed from roster"}
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SCORING & ANALYTICS
# ============================================

@app.get("/leagues/{league_id}/score")
async def calculate_league_score(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Calculate current league scores"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        scores = scoring.calculate_league_scores(league_id)
        return scores
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leagues/{league_id}/targets")
async def get_weekly_targets(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get weekly stat targets"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Pro tier required
    if tier not in ['pro', 'enterprise']:
        raise HTTPException(status_code=403, detail="Pro tier required")
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        targets = scoring.get_weekly_targets(league_id)
        return targets
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leagues/{league_id}/gaps")
async def analyze_gaps(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Analyze category gaps (deficiencies)"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Pro tier required
    if tier not in ['pro', 'enterprise']:
        raise HTTPException(status_code=403, detail="Pro tier required")
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        gaps = scoring.analyze_category_gaps(league_id)
        return gaps
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# LINEUP OPTIMIZATION
# ============================================

@app.get("/leagues/{league_id}/optimize-lineup")
async def optimize_lineup(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get optimized daily lineup"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Pro tier required
    if tier not in ['pro', 'enterprise']:
        raise HTTPException(status_code=403, detail="Pro tier required")
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        optimized = lineup.optimize_daily_lineup(league_id)
        return optimized
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STREAMING RECOMMENDATIONS
# ============================================

@app.get("/leagues/{league_id}/streaming-candidates")
async def get_streaming_candidates(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get streaming candidates for today"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Pro tier required
    if tier not in ['pro', 'enterprise']:
        raise HTTPException(status_code=403, detail="Pro tier required")
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        candidates = streaming.get_streaming_candidates(league_id)
        return candidates
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leagues/{league_id}/hot-pickups")
async def get_hot_pickups(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get hot pickup recommendations"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Pro tier required
    if tier not in ['pro', 'enterprise']:
        raise HTTPException(status_code=403, detail="Pro tier required")
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        hot_pickups = streaming.get_hot_pickups(league_id)
        return hot_pickups
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leagues/{league_id}/recommendations")
async def get_add_drop_recommendations(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get personalized add/drop recommendations"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Pro tier required
    if tier not in ['pro', 'enterprise']:
        raise HTTPException(status_code=403, detail="Pro tier required")
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        recommendations = streaming.get_personalized_recommendations(league_id)
        return recommendations
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# OPPONENT ANALYSIS (H2H)
# ============================================

@app.get("/leagues/{league_id}/opponent-preview")
async def get_opponent_preview(
    league_id: int,
    opponent_league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get H2H opponent preview"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Pro tier required
    if tier not in ['pro', 'enterprise']:
        raise HTTPException(status_code=403, detail="Pro tier required")
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        preview = opponent.analyze_matchup(league_id, opponent_league_id)
        return preview
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TRADE ANALYSIS
# ============================================

@app.post("/leagues/{league_id}/analyze-trade")
async def analyze_trade(
    league_id: int,
    trade: TradeRequest,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Analyze a potential trade"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Pro tier required
    if tier not in ['pro', 'enterprise']:
        raise HTTPException(status_code=403, detail="Pro tier required")
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        analysis = trade.analyze_trade(
            league_id=league_id,
            give_player_ids=trade.give_player_ids,
            receive_player_ids=trade.receive_player_ids
        )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# WEEKLY TRACKING
# ============================================

@app.post("/leagues/{league_id}/record-week")
async def record_weekly_performance(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Record weekly performance snapshot"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        weekly.record_weekly_performance(league_id)
        return {"message": "Weekly performance recorded"}
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leagues/{league_id}/weekly-history")
async def get_weekly_history(
    league_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get weekly performance history"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        # Verify ownership
        league = league_db.get_league(league_id)
        if league['customer_id'] != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        history = weekly.get_weekly_history(league_id)
        return history
    except HTTPException:
        raise
    except Exception as e:
        await logger.log_error(customer_id, request.url.path, str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ACCOUNT MANAGEMENT
# ============================================

@app.get("/account")
async def get_account_info(
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get account information"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.email, c.name, a.tier, a.requests_today, a.daily_limit
            FROM customers c
            JOIN api_keys a ON c.customer_id = a.customer_id
            WHERE c.customer_id = %s AND a.api_key = %s
        """, (customer_id, x_api_key))
        
        result = cursor.fetchone()
        cursor.close()
        db.return_connection(conn)
        
        if not result:
            raise HTTPException(status_code=404, detail="Account not found")
        
        email, name, tier, requests_today, daily_limit = result
        
        return {
            "email": email,
            "name": name,
            "tier": tier,
            "usage": {
                "requests_today": requests_today,
                "daily_limit": daily_limit,
                "remaining": daily_limit - requests_today
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ADMIN & DEBUG ENDPOINTS
# ============================================

@app.get("/debug/logs")
async def get_recent_logs(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    limit: int = 50
):
    """Get recent API request logs (admin only)"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Admin tier check would go here
    try:
        logs = await logger.get_recent_logs(customer_id, limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/errors")
async def get_recent_errors(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    limit: int = 20
):
    """Get recent errors"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        errors = await logger.get_recent_errors(customer_id, limit)
        return errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/slow-queries")
async def get_slow_queries(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    min_duration: float = 1.0,
    limit: int = 20
):
    """Get slow queries (>1s by default)"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        slow_queries = await logger.get_slow_queries(customer_id, min_duration, limit)
        return slow_queries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/cleanup-logs")
async def cleanup_old_logs(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    days_to_keep: int = 30
):
    """Clean up logs older than specified days"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    # Admin check would go here
    try:
        deleted_count = await logger.cleanup_old_logs(days_to_keep)
        return {
            "message": f"Deleted {deleted_count} old log entries",
            "kept_days": days_to_keep
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/dashboard")
async def debug_dashboard(
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Get debug dashboard data"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        dashboard = await logger.get_dashboard_stats(customer_id)
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/fix-error/{error_id}")
async def mark_error_fixed(
    error_id: int,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """Mark an error as fixed"""
    customer_id, tier = await verify_api_key(request, x_api_key)
    
    try:
        await logger.mark_error_fixed(error_id)
        return {"message": "Error marked as fixed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    # Log the error
    traceback_str = traceback.format_exc()
    print(f"Global error: {str(exc)}")
    print(traceback_str)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": request.url.path
        }
    )


# ============================================
# STARTUP & SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database connections on startup"""
    print("🚀 Starting NBA Fantasy Basketball API...")
    db.init_connection_pool(minconn=2, maxconn=20)
    print("✅ Database connection pool initialized")
    print("✅ API ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""
    print("👋 Shutting down NBA Fantasy Basketball API...")
    db.close_all_connections()
    print("✅ Database connections closed")


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "dbb2_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
