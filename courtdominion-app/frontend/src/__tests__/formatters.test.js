import { describe, it, expect } from 'vitest'
import { formatPercentage, formatDecimal } from '../utils/formatters'

describe('Formatters Utility', () => {
  describe('formatPercentage', () => {
    it('formats decimal to percentage', () => {
      expect(formatPercentage(0.582)).toBe('58.2%')
    })

    it('handles zero', () => {
      expect(formatPercentage(0)).toBe('0.0%')
    })

    it('handles one', () => {
      expect(formatPercentage(1.0)).toBe('100.0%')
    })

    it('handles null/undefined gracefully', () => {
      expect(formatPercentage(null)).toBe('0.0%')
      expect(formatPercentage(undefined)).toBe('0.0%')
    })
  })

  describe('formatDecimal', () => {
    it('formats number to one decimal place', () => {
      expect(formatDecimal(27.456)).toBe('27.5')
    })

    it('handles integers', () => {
      expect(formatDecimal(27)).toBe('27.0')
    })

    it('handles null/undefined gracefully', () => {
      expect(formatDecimal(null)).toBe('0.0')
      expect(formatDecimal(undefined)).toBe('0.0')
    })
  })
})
