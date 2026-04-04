interface Props {
  message: string
  isBot: boolean
  timestamp?: Date
}

export default function ChatMessage({ message, isBot, timestamp }: Props) {
  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} mb-3`}>
      <div
        className={`max-w-[85%] px-4 py-3 rounded-xl text-sm leading-relaxed whitespace-pre-wrap ${
          isBot
            ? 'bg-slate-100 text-slate-800 rounded-tl-sm'
            : 'bg-amber-500 text-white rounded-tr-sm'
        }`}
      >
        {isBot && (
          <div className="flex items-center gap-1.5 mb-1.5">
            <div className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center">
              <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <span className="text-xs font-semibold text-emerald-600">ZoneGuard</span>
          </div>
        )}
        <p>{message}</p>
        {timestamp && (
          <p className={`text-xs mt-1.5 ${isBot ? 'text-slate-400' : 'text-amber-200'}`}>
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </div>
  )
}
