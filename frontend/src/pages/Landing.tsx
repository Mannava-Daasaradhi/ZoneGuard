import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col items-center justify-center px-4 relative overflow-hidden">
      {/* Ambient grid background */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M 60 0 L 0 0 0 60' fill='none' stroke='%23475569' stroke-width='1'/%3E%3C/svg%3E")`,
        }}
      />

      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="relative z-10 text-center mb-8 sm:mb-12 px-2">
        <div className="flex items-center justify-center gap-3 mb-4 sm:mb-6">
          <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-amber-500 flex items-center justify-center shadow-lg shadow-amber-500/30">
            <svg className="w-6 h-6 sm:w-7 sm:h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">ZoneGuard</h1>
        </div>
        <p className="text-slate-300 text-base sm:text-lg max-w-md mx-auto leading-relaxed">
          When the zone goes dark,{' '}
          <span className="text-amber-400 font-semibold">your income doesn't have to.</span>
        </p>
        <p className="text-slate-500 text-xs sm:text-sm mt-2 sm:mt-3">
          AI-powered parametric income protection for Amazon Flex riders · Bengaluru
        </p>
      </div>

      {/* Persona cards */}
      <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5 w-full max-w-2xl">
        {/* Rider card */}
        <button
          onClick={() => navigate('/rider')}
          className="group bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6 sm:p-8 text-left hover:bg-amber-500/20 hover:border-amber-400 transition-all duration-200 hover:shadow-2xl hover:shadow-amber-500/10 hover:-translate-y-1 active:translate-y-0"
        >
          <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center mb-4 group-hover:bg-amber-500/30 transition-colors text-2xl">
            🛵
          </div>
          <h2 className="text-white font-bold text-xl mb-2">I'm a Rider</h2>
          <p className="text-slate-400 text-sm leading-relaxed mb-4">
            View your weekly coverage, track zone signals, and see your payout history
          </p>
          <div className="flex items-center gap-2 text-amber-400 text-sm font-medium">
            <span>Enter Rider Dashboard</span>
            <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>

        {/* Insurer card */}
        <button
          onClick={() => navigate('/admin')}
          className="group bg-blue-500/10 border border-blue-500/30 rounded-2xl p-6 sm:p-8 text-left hover:bg-blue-500/20 hover:border-blue-400 transition-all duration-200 hover:shadow-2xl hover:shadow-blue-500/10 hover:-translate-y-1 active:translate-y-0"
        >
          <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-4 group-hover:bg-blue-500/30 transition-colors text-2xl">
            📊
          </div>
          <h2 className="text-white font-bold text-xl mb-2">I'm an Insurer</h2>
          <p className="text-slate-400 text-sm leading-relaxed mb-4">
            Monitor zone risk, manage the QuadSignal engine, review claims, and track loss ratios
          </p>
          <div className="flex items-center gap-2 text-blue-400 text-sm font-medium">
            <span>Enter Admin Dashboard</span>
            <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>
      </div>

      {/* Stats strip */}
      <div className="relative z-10 mt-10 grid grid-cols-2 sm:flex sm:items-center gap-4 sm:gap-8 text-center w-full max-w-2xl px-4 sm:px-0">
        {[
          ['1,624', 'Active policies'],
          ['10', 'Zones monitored'],
          ['< 2 hrs', 'Avg payout time'],
          ['₹39–₹225', 'Weekly premiums'],
        ].map(([val, label]) => (
          <div key={label} className="bg-white/5 rounded-xl p-3 sm:bg-transparent sm:p-0">
            <p className="text-white font-bold text-lg">{val}</p>
            <p className="text-slate-500 text-xs">{label}</p>
          </div>
        ))}
      </div>

      {/* Onboarding link */}
      <div className="relative z-10 mt-8">
        <button
          onClick={() => navigate('/onboarding')}
          className="text-slate-500 hover:text-amber-400 text-sm transition-colors underline underline-offset-4"
        >
          New rider? Get covered in 90 seconds →
        </button>
      </div>
    </div>
  )
}
