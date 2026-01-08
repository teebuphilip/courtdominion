import { useState } from 'react'
import { Mail, Check } from 'lucide-react'

const EmailCapture = ({ onUnlock }) => {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!email) return

    // Set localStorage flag to unlock projections
    localStorage.setItem('cd_email_captured', 'true')
    setSubmitted(true)

    // Call onUnlock callback if provided (for ProjectionsPage)
    if (onUnlock) {
      onUnlock()
    }

    // TODO: Integrate with MailerLite/Mailchimp/Buttondown API
    // For now, just unlocks the content
  }

  if (submitted) {
    return (
      <div className="py-16 bg-gray-900">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gray-800 rounded-lg p-8 border border-green-700">
            <div className="text-center">
              <div className="inline-flex p-3 bg-green-500/20 rounded-full mb-4">
                <Check className="h-8 w-8 text-green-500" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">
                You're All Set!
              </h2>
              <p className="text-gray-400">
                Access unlocked. Enjoy your projections!
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="py-16 bg-gray-900">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gray-800 rounded-lg p-8 border border-gray-700">
          <div className="text-center mb-6">
            <div className="inline-flex p-3 bg-primary-500/20 rounded-full mb-4">
              <Mail className="h-8 w-8 text-primary-500" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">
              Get Daily NBA Fantasy Insights
            </h2>
            <p className="text-gray-400">
              Join our mailing list for daily projections and waiver wire recommendations
            </p>
          </div>

          <div className="max-w-md mx-auto">
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="sr-only">
                  Email address
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-gray-800"
              >
                Subscribe Now
              </button>
            </form>

            <p className="mt-4 text-xs text-gray-500 text-center">
              We respect your privacy. Unsubscribe at any time.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EmailCapture
