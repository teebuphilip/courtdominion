import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Header from '../components/layout/Header'

describe('Header navigation', () => {
  it('includes links to new public pages', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    )

    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Projections' })).toHaveAttribute('href', '/projections')
    expect(screen.getByRole('link', { name: 'Public Model' })).toHaveAttribute('href', '/public-model')
    expect(screen.getByRole('link', { name: 'Historical Bets' })).toHaveAttribute('href', '/historical-bets')
    expect(screen.getByRole('link', { name: "Today's Bets" })).toHaveAttribute('href', '/todays-bets')
  })
})
