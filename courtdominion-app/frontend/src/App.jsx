import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import HomePage from './pages/HomePage'
import ProjectionsPage from './pages/ProjectionsPage'
import PlayerDetailPage from './pages/PlayerDetailPage'
import PublicModelPage from './pages/PublicModelPage'
import HistoricalBetsPage from './pages/HistoricalBetsPage'
import TodaysBetsPage from './pages/TodaysBetsPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/projections" element={<ProjectionsPage />} />
        <Route path="/public-model" element={<PublicModelPage />} />
        <Route path="/historical-bets" element={<HistoricalBetsPage />} />
        <Route path="/todays-bets" element={<TodaysBetsPage />} />
        <Route path="/player/:playerId" element={<PlayerDetailPage />} />
      </Routes>
    </Layout>
  )
}

export default App
