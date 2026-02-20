const TodaysBetsPage = () => {
  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Today's Bets</h1>
          <p className="text-xl text-gray-400">
            Track the current day bet slate across sportsbook, Kalshi, and exchange picks.
          </p>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          <iframe
            title="Today's Bets"
            src="/todays-bets.html"
            className="w-full h-[76vh] bg-white"
          />
        </div>
      </div>
    </div>
  )
}

export default TodaysBetsPage
