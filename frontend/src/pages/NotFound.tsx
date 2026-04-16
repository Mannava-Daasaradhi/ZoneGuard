import { useNavigate } from 'react-router-dom'

export default function NotFound() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <p className="text-6xl font-bold text-slate-700 mb-4">404</p>
        <h1 className="text-white text-xl font-bold mb-2">Page not found</h1>
        <p className="text-slate-400 text-sm mb-6">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <button
          onClick={() => navigate('/')}
          className="bg-amber-500 hover:bg-amber-400 text-white text-sm font-semibold px-6 py-2.5 rounded-lg transition-colors"
        >
          Back to Home
        </button>
      </div>
    </div>
  )
}
