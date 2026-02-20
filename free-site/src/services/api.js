import axios from 'axios'

// Base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Mock data flag - set to false to use real API (production mode)
const USE_MOCK_DATA = false

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Mock data generators
const generateMockPlayers = () => {
  const teams = ['LAL', 'BOS', 'GSW', 'MIL', 'PHI', 'DEN', 'MIA', 'DAL', 'PHX', 'NYK']
  const positions = ['G', 'F', 'C', 'F-G', 'G-F', 'F-C']
  const firstNames = ['LeBron', 'Stephen', 'Giannis', 'Kevin', 'Luka', 'Nikola', 'Joel', 'Jayson', 'Damian', 'Anthony']
  const lastNames = ['James', 'Curry', 'Antetokounmpo', 'Durant', 'Doncic', 'Jokic', 'Embiid', 'Tatum', 'Lillard', 'Davis']
  
  return Array.from({ length: 398 }, (_, i) => ({
    id: `20${String(i).padStart(4, '0')}`,
    name: `${firstNames[i % 10]} ${lastNames[Math.floor(Math.random() * 10)]}`,
    team: teams[i % teams.length],
    position: positions[i % positions.length],
    age: 20 + Math.floor(Math.random() * 15),
    status: 'active'
  }))
}

const generateMockProjections = () => {
  const mockPlayers = generateMockPlayers()
  return mockPlayers.map(player => ({
    player_id: player.id,
    name: player.name,
    team: player.team,
    position: player.position,
    fantasy_points: Number((Math.random() * 50 + 10).toFixed(1)),
    minutes: Number((Math.random() * 20 + 15).toFixed(1)),
    points: Number((Math.random() * 20 + 5).toFixed(1)),
    rebounds: Number((Math.random() * 10 + 2).toFixed(1)),
    assists: Number((Math.random() * 8 + 1).toFixed(1)),
    steals: Number((Math.random() * 2 + 0.5).toFixed(1)),
    blocks: Number((Math.random() * 2 + 0.3).toFixed(1)),
    turnovers: Number((Math.random() * 3 + 1).toFixed(1)),
    fg_pct: Number((Math.random() * 0.2 + 0.4).toFixed(3)),
    ft_pct: Number((Math.random() * 0.25 + 0.65).toFixed(3)),
    three_pointers: Number((Math.random() * 3 + 0.5).toFixed(1)),
    confidence: Number((Math.random() * 0.3 + 0.7).toFixed(2))
  }))
}

const MOCK_DATA = {
  content: {
    homepage: {
      headline: "NBA Fantasy Projections Built Different",
      subheadline: "Risk analysis, volatility metrics, and waiver wire intelligence",
      value_props: [
        "Risk-adjusted projections you can trust",
        "Volatility indicators for every player",
        "Daily waiver wire insights"
      ],
      cta_primary: "View Today's Projections",
      cta_secondary: "Get Daily Insights"
    },
    projections_page: {
      title: "Daily Projections",
      subtitle: "398 NBA players with risk-adjusted fantasy points"
    },
    insights_page: {
      title: "Waiver Wire Insights",
      subtitle: "Deep sleepers and value plays for your league"
    },
    player_detail: {
      stats_title: "Season Averages",
      risk_title: "Risk Analysis"
    }
  },
  
  projections: generateMockProjections(),
  
  insights: [
    {
      player_id: "200001",
      name: "Jordan Clarkson",
      team: "UTA",
      position: "G",
      insight_type: "waiver_wire",
      value_score: 8.7,
      recommendation: "Add immediately",
      reasoning: "High usage rate with efficient scoring. Minutes trending up with recent injury to starting PG.",
      trending: "up",
      ownership_estimate: "45%"
    },
    {
      player_id: "200002",
      name: "Bobby Portis",
      team: "MIL",
      position: "F",
      insight_type: "sleeper",
      value_score: 7.9,
      recommendation: "Strong add",
      reasoning: "Consistent double-double threat when in starting lineup. Great percentages and rebounds.",
      trending: "stable",
      ownership_estimate: "62%"
    },
    {
      player_id: "200003",
      name: "Caris LeVert",
      team: "CLE",
      position: "G-F",
      insight_type: "streaming",
      value_score: 7.2,
      recommendation: "Stream for tonight",
      reasoning: "Favorable matchup against bottom-5 defensive team. Secondary ball handler role.",
      trending: "up",
      ownership_estimate: "38%"
    }
  ],
  
  risk: [
    {
      player_id: "200001",
      name: "LeBron James",
      injury_risk: "medium",
      consistency: 88,
      ceiling: 62.5,
      floor: 32.8,
      volatility: 0.18,
      recommendation: "High floor, moderate ceiling"
    }
  ]
}

// API functions
export const fetchContent = async () => {
  if (USE_MOCK_DATA) {
    return new Promise(resolve => 
      setTimeout(() => resolve({ data: MOCK_DATA.content }), 300)
    )
  }
  return api.get('/api/content')
}

const statNum = (value, fallback = 0) => {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

const toFantasyPoints = (p) => {
  const points = statNum(p.pts)
  const rebounds = statNum(p.reb)
  const assists = statNum(p.ast)
  const steals = statNum(p.stl)
  const blocks = statNum(p.blk)
  const turnovers = 0

  return Number(
    (
      points * 1.0 +
      rebounds * 1.2 +
      assists * 1.5 +
      steals * 3.0 +
      blocks * 3.0 -
      turnovers
    ).toFixed(1)
  )
}

const avgConfidence = (p) => {
  const confs = [
    statNum(p.pts_conf, 0.4),
    statNum(p.reb_conf, 0.4),
    statNum(p.ast_conf, 0.4),
    statNum(p.fg3m_conf, 0.4),
    statNum(p.stl_conf, 0.4),
    statNum(p.blk_conf, 0.4),
  ]
  return confs.reduce((sum, c) => sum + c, 0) / confs.length
}

const confidenceToRiskLabel = (conf) => {
  if (conf >= 0.75) return 'low'
  if (conf >= 0.6) return 'medium'
  return 'high'
}

const mapTodayProjectionPlayer = (p) => ({
  player_id: String(p.id),
  name: p.name,
  team: p.team,
  position: p.position,
  fantasy_points: toFantasyPoints(p),
  minutes: 0,
  points: statNum(p.pts),
  rebounds: statNum(p.reb),
  assists: statNum(p.ast),
  steals: statNum(p.stl),
  blocks: statNum(p.blk),
  turnovers: 0,
  fg_pct: 0,
  ft_pct: 0,
  three_pointers: statNum(p.fg3m),
  confidence: Number(avgConfidence(p).toFixed(2)),
})

const toPlayerRisk = (mappedProjection, rawProjection) => {
  const conf = avgConfidence(rawProjection)
  const fpStd = Math.sqrt(
    Math.max(
      0,
      statNum(rawProjection.pts_std) ** 2 +
      (1.2 * statNum(rawProjection.reb_std)) ** 2 +
      (1.5 * statNum(rawProjection.ast_std)) ** 2 +
      (3.0 * statNum(rawProjection.stl_std)) ** 2 +
      (3.0 * statNum(rawProjection.blk_std)) ** 2
    )
  )
  const floor = Math.max(0, Number((mappedProjection.fantasy_points - fpStd).toFixed(1)))
  const ceiling = Number((mappedProjection.fantasy_points + fpStd).toFixed(1))
  const volatility = mappedProjection.fantasy_points > 0
    ? Number((fpStd / mappedProjection.fantasy_points).toFixed(2))
    : 0.4
  const consistency = Math.round(conf * 100)

  return {
    injury_risk: confidenceToRiskLabel(conf),
    consistency,
    ceiling,
    floor,
    volatility,
    recommendation:
      consistency >= 75
        ? 'Stable profile for tonight.'
        : consistency >= 60
          ? 'Playable, but expect moderate variance.'
          : 'High variance profile; size exposure carefully.',
  }
}

const fetchTodayProjectionsRaw = async () => {
  const response = await api.get('/projections/today')
  return Array.isArray(response?.data?.players) ? response.data.players : []
}

export const fetchProjections = async (params = {}) => {
  if (USE_MOCK_DATA) {
    const { limit = 100, offset = 0, sort_by = 'fantasy_points', order = 'desc' } = params
    let projections = [...MOCK_DATA.projections]
    
    // Sort
    projections.sort((a, b) => {
      const aVal = a[sort_by] || 0
      const bVal = b[sort_by] || 0
      return order === 'desc' ? bVal - aVal : aVal - bVal
    })
    
    // Paginate
    const paginatedProjections = projections.slice(offset, offset + limit)
    
    return new Promise(resolve =>
      setTimeout(() => resolve({
        data: {
          projections: paginatedProjections,
          total: projections.length,
          limit,
          offset,
          last_updated: new Date().toISOString()
        }
      }), 500)
    )
  }

  const { limit = 100, offset = 0, sort_by = 'fantasy_points', order = 'desc' } = params
  const rawPlayers = await fetchTodayProjectionsRaw()
  const projections = rawPlayers.map(mapTodayProjectionPlayer)

  projections.sort((a, b) => {
    const aVal = a[sort_by] ?? 0
    const bVal = b[sort_by] ?? 0

    if (typeof aVal === 'string' || typeof bVal === 'string') {
      return order === 'desc'
        ? String(bVal).localeCompare(String(aVal))
        : String(aVal).localeCompare(String(bVal))
    }
    return order === 'desc' ? bVal - aVal : aVal - bVal
  })

  const paginated = projections.slice(offset, offset + limit)
  return {
    data: {
      projections: paginated,
      total: projections.length,
      limit,
      offset,
      last_updated: new Date().toISOString(),
    }
  }
}

export const fetchPlayer = async (playerId) => {
  if (USE_MOCK_DATA) {
    const projection = MOCK_DATA.projections.find(p => p.player_id === playerId)
    if (!projection) {
      throw new Error('Player not found')
    }
    
    const player = {
      id: projection.player_id,
      name: projection.name,
      team: projection.team,
      position: projection.position,
      age: 25,
      status: 'active',
      projection: {
        fantasy_points: projection.fantasy_points,
        minutes: projection.minutes,
        points: projection.points,
        rebounds: projection.rebounds,
        assists: projection.assists,
        steals: projection.steals,
        blocks: projection.blocks,
        turnovers: projection.turnovers,
        fg_pct: projection.fg_pct,
        ft_pct: projection.ft_pct,
        three_pointers: projection.three_pointers
      },
      insight: {
        value_score: Number((Math.random() * 3 + 7).toFixed(1)),
        recommendation: "Strong start",
        trending: "up"
      },
      risk: {
        injury_risk: ["low", "medium", "high"][Math.floor(Math.random() * 3)],
        consistency: Math.floor(Math.random() * 30 + 70),
        ceiling: projection.fantasy_points * 1.3,
        floor: projection.fantasy_points * 0.7,
        volatility: Number((Math.random() * 0.2 + 0.1).toFixed(2)),
        recommendation: "Reliable contributor"
      }
    }
    
    return new Promise(resolve =>
      setTimeout(() => resolve({ data: player }), 400)
    )
  }

  const rawPlayers = await fetchTodayProjectionsRaw()
  const raw = rawPlayers.find((p) => String(p.id) === String(playerId))

  if (!raw) {
    const error = new Error('Player not found')
    error.status = 404
    throw error
  }

  const mapped = mapTodayProjectionPlayer(raw)
  const risk = toPlayerRisk(mapped, raw)

  return {
    data: {
      id: mapped.player_id,
      name: mapped.name,
      team: mapped.team,
      position: mapped.position,
      status: 'active',
      fantasy_points: mapped.fantasy_points,
      projection: {
        fantasy_points: mapped.fantasy_points,
        minutes: mapped.minutes,
        points: mapped.points,
        rebounds: mapped.rebounds,
        assists: mapped.assists,
        steals: mapped.steals,
        blocks: mapped.blocks,
        turnovers: mapped.turnovers,
        fg_pct: mapped.fg_pct,
        ft_pct: mapped.ft_pct,
        three_pointers: mapped.three_pointers,
      },
      insight: {
        value_score: Number((Math.min(10, Math.max(1, mapped.fantasy_points / 6))).toFixed(1)),
        recommendation: risk.recommendation,
        trending: 'stable',
      },
      risk,
    }
  }
}

export const fetchInsights = async (params = {}) => {
  if (USE_MOCK_DATA) {
    return new Promise(resolve =>
      setTimeout(() => resolve({
        data: {
          insights: MOCK_DATA.insights,
          count: MOCK_DATA.insights.length,
          category: params.category || 'all'
        }
      }), 400)
    )
  }

  const category = params.category || 'all'
  const rawPlayers = await fetchTodayProjectionsRaw()

  const insights = rawPlayers
    .map((raw) => {
      const mapped = mapTodayProjectionPlayer(raw)
      const conf = avgConfidence(raw)
      const valueScore = Number((Math.min(10, Math.max(1, mapped.fantasy_points / 6))).toFixed(1))
      const riskLabel = confidenceToRiskLabel(conf)

      return {
        player_id: mapped.player_id,
        name: mapped.name,
        team: mapped.team,
        position: mapped.position,
        value_score: valueScore,
        recommendation:
          category === 'avoid' || riskLabel === 'high'
            ? 'Avoid unless you need upside'
            : valueScore >= 8
              ? 'Strong add'
              : 'Consider stream',
        reasoning: `Projection ${mapped.fantasy_points} FPTS with ${Math.round(conf * 100)}% confidence.`,
        trending: conf >= 0.75 ? 'up' : conf < 0.6 ? 'down' : 'stable',
        ownership_estimate: `${Math.round(Math.min(95, Math.max(5, valueScore * 10)))}%`,
      }
    })
    .sort((a, b) => b.value_score - a.value_score)

  const filtered = insights.filter((item) => {
    if (category === 'all') return true
    if (category === 'high_value') return item.value_score >= 8
    if (category === 'sleepers') return item.value_score >= 6.5 && item.value_score < 8
    if (category === 'avoid') return item.trending === 'down'
    return true
  })

  return {
    data: {
      insights: filtered.slice(0, 30),
      count: filtered.length,
      category,
    }
  }
}

export const fetchRisk = async (playerId) => {
  if (USE_MOCK_DATA) {
    const risk = MOCK_DATA.risk[0]
    return new Promise(resolve =>
      setTimeout(() => resolve({ data: risk }), 300)
    )
  }

  const rawPlayers = await fetchTodayProjectionsRaw()
  const raw = rawPlayers.find((p) => String(p.id) === String(playerId))
  if (!raw) {
    const error = new Error('Player not found')
    error.status = 404
    throw error
  }

  const mapped = mapTodayProjectionPlayer(raw)
  return { data: toPlayerRisk(mapped, raw) }
}

export const searchPlayers = async (query) => {
  if (USE_MOCK_DATA) {
    const filtered = MOCK_DATA.projections.filter(p =>
      p.name.toLowerCase().includes(query.toLowerCase())
    )
    return new Promise(resolve =>
      setTimeout(() => resolve({
        data: {
          players: filtered.slice(0, 20),
          count: filtered.length
        }
      }), 200)
    )
  }

  const q = String(query || '').trim().toLowerCase()
  if (!q) {
    return { data: { players: [], count: 0 } }
  }

  const rawPlayers = await fetchTodayProjectionsRaw()
  const players = rawPlayers
    .map(mapTodayProjectionPlayer)
    .filter((p) =>
      p.name.toLowerCase().includes(q) ||
      p.team.toLowerCase().includes(q) ||
      p.position.toLowerCase().includes(q)
    )
    .slice(0, 20)

  return {
    data: {
      players,
      count: players.length,
    }
  }
}

export default api
