import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import HomePage from './pages/HomePage'
import ProjectionsPage from './pages/ProjectionsPage'
import PlayerDetailPage from './pages/PlayerDetailPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/projections" element={<ProjectionsPage />} />
        <Route path="/player/:playerId" element={<PlayerDetailPage />} />
      </Routes>
    </Layout>
  )
}

export default App
