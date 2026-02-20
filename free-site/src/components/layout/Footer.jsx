const Footer = () => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-gray-800 border-t border-gray-700 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <h3 className="text-xl font-bold mb-4">
              <span className="text-primary-500">Court</span>
              <span className="text-white">Dominion</span>
            </h3>
            <p className="text-gray-400 text-sm">
              Risk-adjusted NBA fantasy basketball projections with volatility metrics and waiver wire intelligence.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/projections" className="text-gray-400 hover:text-primary-500 transition-colors">
                  Daily Projections
                </a>
              </li>
              <li>
                <a href="/insights" className="text-gray-400 hover:text-primary-500 transition-colors">
                  Waiver Wire Insights
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-white font-semibold mb-4">Information</h4>
            <p className="text-gray-400 text-sm mb-2">
              Phase 1 MVP - January 2026
            </p>
            <p className="text-gray-400 text-xs">
              Data updated daily at 5am EST
            </p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-700">
          <p className="text-center text-gray-400 text-sm">
            © {currentYear} CourtDominion. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
