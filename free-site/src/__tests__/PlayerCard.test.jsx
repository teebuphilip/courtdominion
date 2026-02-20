import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import PlayerCard from '../components/player/PlayerCard'

const mockPlayer = {
  player_id: '203999',
  name: 'Nikola Jokic',
  team: 'DEN',
  position: 'C',
  fantasy_points: 58.3,
  points_per_game: 27.0,
  rebounds_per_game: 13.2,
  assists_per_game: 8.8,
}

describe('PlayerCard Component', () => {
  it('renders player name', () => {
    render(
      <BrowserRouter>
        <PlayerCard player={mockPlayer} />
      </BrowserRouter>
    )

    expect(screen.getByText('Nikola Jokic')).toBeInTheDocument()
  })

  it('renders player team and position', () => {
    render(
      <BrowserRouter>
        <PlayerCard player={mockPlayer} />
      </BrowserRouter>
    )

    expect(screen.getByText(/DEN/)).toBeInTheDocument()
    expect(screen.getByText(/C/)).toBeInTheDocument()
  })

  it('renders fantasy points', () => {
    render(
      <BrowserRouter>
        <PlayerCard player={mockPlayer} />
      </BrowserRouter>
    )

    expect(screen.getByText(/58.3/)).toBeInTheDocument()
  })

  it('renders with minimal data', () => {
    const minimalPlayer = {
      player_id: '12345',
      name: 'Test Player',
      team: 'LAL',
      position: 'PG',
    }

    render(
      <BrowserRouter>
        <PlayerCard player={minimalPlayer} />
      </BrowserRouter>
    )

    expect(screen.getByText('Test Player')).toBeInTheDocument()
  })
})
