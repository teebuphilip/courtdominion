import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import HistoricalBetsPage from '../pages/HistoricalBetsPage'
import TodaysBetsPage from '../pages/TodaysBetsPage'
import PublicModelPage from '../pages/PublicModelPage'

describe('Bet landing pages', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders historical bets page shell', () => {
    render(<HistoricalBetsPage />)

    expect(screen.getByRole('heading', { name: 'Historical Bets' })).toBeInTheDocument()
    expect(screen.getByText(/archived graded results/i)).toBeInTheDocument()
  })

  it("renders today's bets page shell", () => {
    render(<TodaysBetsPage />)

    expect(screen.getByRole('heading', { name: "Today's Bets" })).toBeInTheDocument()
    expect(screen.getByText(/current-day bet slate/i)).toBeInTheDocument()
  })

  it('renders public model iframe with correct source', () => {
    render(<PublicModelPage />)

    expect(screen.getByRole('heading', { name: 'Public DFS Model' })).toBeInTheDocument()
    expect(screen.getByTitle('Public DFS Model')).toHaveAttribute('src', '/dfsrase-public-model.html')
  })
})
