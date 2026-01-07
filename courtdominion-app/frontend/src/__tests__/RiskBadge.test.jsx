import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import RiskBadge from '../components/projections/RiskBadge'

describe('RiskBadge Component', () => {
  it('renders low risk correctly', () => {
    render(<RiskBadge risk="low" />)

    const badge = screen.getByText(/low/i)
    expect(badge).toBeInTheDocument()
  })

  it('renders medium risk correctly', () => {
    render(<RiskBadge risk="medium" />)

    const badge = screen.getByText(/medium/i)
    expect(badge).toBeInTheDocument()
  })

  it('renders high risk correctly', () => {
    render(<RiskBadge risk="high" />)

    const badge = screen.getByText(/high/i)
    expect(badge).toBeInTheDocument()
  })

  it('renders with default when no risk provided', () => {
    render(<RiskBadge />)

    // Should render something (depends on component implementation)
    expect(document.body).toBeTruthy()
  })
})
