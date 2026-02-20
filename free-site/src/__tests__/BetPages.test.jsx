import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import HistoricalBetsPage from '../pages/HistoricalBetsPage'
import TodaysBetsPage from '../pages/TodaysBetsPage'

describe('Bet landing pages', () => {
  it('renders historical bets iframe with correct source', () => {
    render(<HistoricalBetsPage />)

    expect(screen.getByRole('heading', { name: 'Historical Bets' })).toBeInTheDocument()
    expect(screen.getByTitle('Historical Bets')).toHaveAttribute('src', '/historical-bets.html')
  })

  it("renders today's bets iframe with correct source", () => {
    render(<TodaysBetsPage />)

    expect(screen.getByRole('heading', { name: "Today's Bets" })).toBeInTheDocument()
    expect(screen.getByTitle("Today's Bets")).toHaveAttribute('src', '/todays-bets.html')
  })
})
