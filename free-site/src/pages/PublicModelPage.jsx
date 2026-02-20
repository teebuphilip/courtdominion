const PublicModelPage = () => {
  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Public DFS Model</h1>
          <p className="text-xl text-gray-400">
            Read-only bankroll model (v1) with deterministic daily rules.
          </p>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          <iframe
            title="Public DFS Model"
            src="/dfsrase-public-model.html"
            className="w-full h-[76vh] bg-white"
          />
        </div>
      </div>
    </div>
  )
}

export default PublicModelPage
