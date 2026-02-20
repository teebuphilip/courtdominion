import Hero from '../components/home/Hero'
import ValueProps from '../components/home/ValueProps'
import EmailCapture from '../components/home/EmailCapture'
import SocialProof from '../components/home/SocialProof'
import { useContent } from '../hooks/useContent'

const HomePage = () => {
  const { data: content, isLoading } = useContent()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div>
      <Hero content={content?.homepage} />
      <ValueProps content={content?.homepage} />
      <SocialProof />
      <EmailCapture />
    </div>
  )
}

export default HomePage
