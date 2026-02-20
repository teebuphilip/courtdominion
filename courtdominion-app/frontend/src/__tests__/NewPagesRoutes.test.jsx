import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'

describe('New page routes', () => {
  it('renders public model page', () => {
    render(
      <MemoryRouter initialEntries={['/public-model']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByRole('heading', { name: 'Public DFS Model' })).toBeInTheDocument()
    expect(screen.getByTitle('Public DFS Model')).toHaveAttribute('src', '/dfsrase-public-model.html')
  })

  it('renders historical bets page', () => {
    render(
      <MemoryRouter initialEntries={['/historical-bets']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByRole('heading', { name: 'Historical Bets' })).toBeInTheDocument()
    expect(screen.getByTitle('Historical Bets')).toHaveAttribute('src', '/historical-bets.html')
  })

  it("renders today's bets page", () => {
    render(
      <MemoryRouter initialEntries={['/todays-bets']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByRole('heading', { name: "Today's Bets" })).toBeInTheDocument()
    expect(screen.getByTitle("Today's Bets")).toHaveAttribute('src', '/todays-bets.html')
  })
})
