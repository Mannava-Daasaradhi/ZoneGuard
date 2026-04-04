export interface ChatResponse {
  keywords: string[]
  response: string
}

export const CHAT_RESPONSES: ChatResponse[] = [
  {
    keywords: ['claim status', 'my claim', 'claim update', 'status'],
    response: 'Your latest claim is APPROVED ✅. Payout: ₹1,950 credited via UPI (Ref: ZG-2026-3819). Processing time: 47 minutes. View full history in your dashboard.'
  },
  {
    keywords: ['how payout', 'payout calculated', 'payout work', 'calculation', 'how much'],
    response: 'You receive 75% of your 7-day average daily earnings when all 4 signals fire (HIGH confidence). For MEDIUM confidence (3 signals), you get 65%. Your current baseline: ₹2,600/day → Max payout: ₹1,950/disruption day.'
  },
  {
    keywords: ['what covered', 'coverage', 'what is covered', 'covered events', 'protection'],
    response: 'ZoneGuard covers income loss from:\n• 🌊 Flash floods (water-logging >6 inches)\n• 💨 Severe AQI (>300 hazardous)\n• 🚧 Transport strikes (metro/bus >50% off)\n• 🛣️ Road closures (major arterials)\n• 🌧️ Extreme weather (heavy rain >65mm/hr)\n\nAll verified by our 4-signal fusion system.'
  },
  {
    keywords: ['not covered', 'exclusion', 'excluded', 'what not', 'exceptions'],
    response: 'Exclusions include:\n• ❌ War, civil unrest, terrorism\n• ❌ Pandemic/epidemic declarations\n• ❌ Vehicle mechanical failures\n• ❌ Personal illness or injury\n• ❌ Voluntary work stoppage\n• ❌ Events outside your registered zone\n\nFull policy terms available in your dashboard.'
  },
  {
    keywords: ['when money', 'when paid', 'payout time', 'how long', 'disbursement'],
    response: 'HIGH confidence claims (4/4 signals) are paid within 2 hours automatically via UPI. MEDIUM confidence claims (3/4 signals) are reviewed within 4 hours by our team. You\'ll receive SMS + app notification when funds are credited.'
  },
  {
    keywords: ['premium', 'cost', 'price', 'how much pay', 'weekly cost'],
    response: 'Your weekly premium depends on zone risk tier:\n• 🟢 Low risk: ₹29/week\n• 🟡 Medium risk: ₹49/week\n• 🟠 High risk: ₹69/week\n• 🔴 Flood-prone: ₹99/week\n\nPremium auto-deducts every Monday. Skip any week—no lock-in!'
  },
  {
    keywords: ['signal', 'signals', '4 signals', 'how work', 'quad signal'],
    response: 'ZoneGuard uses 4 independent signals:\n• S1 🌧️ Environmental (weather sensors)\n• S2 🚗 Mobility (traffic/road data)\n• S3 📦 Economic (order volumes)\n• S4 👥 Crowd (rider check-ins)\n\nWhen 3-4 signals breach thresholds, your claim auto-triggers!'
  },
  {
    keywords: ['help', 'support', 'contact', 'talk to human', 'agent'],
    response: 'I can help with:\n• 📋 Claim status & history\n• 💰 Payout calculations\n• 🛡️ Coverage details\n• ❓ General questions\n\nNeed human support? Call 1800-ZONEGUARD or email support@zoneguard.in (9am-9pm IST).'
  },
  {
    keywords: ['hello', 'hi', 'hey', 'good morning', 'good evening'],
    response: 'Hello! 👋 I\'m your ZoneGuard Assistant. I can help you with claim status, payouts, coverage questions, and more. What would you like to know?'
  },
  {
    keywords: ['thank', 'thanks', 'bye', 'goodbye'],
    response: 'You\'re welcome! 🙏 Stay safe out there. Remember—ZoneGuard has your back when disruptions hit. Ride safe!'
  }
]

export const DEFAULT_RESPONSE = 'I can help with claim status, payouts, and coverage questions. Try asking:\n• "What\'s my claim status?"\n• "How is payout calculated?"\n• "What events are covered?"\n\nOr tap a quick action below! 👇'

export const WELCOME_MESSAGE = 'Hi! 👋 I\'m your ZoneGuard Assistant. I can help you with claims, payouts, and coverage questions. How can I help you today?'

export function findResponse(input: string): string {
  const normalizedInput = input.toLowerCase().trim()
  
  for (const item of CHAT_RESPONSES) {
    for (const keyword of item.keywords) {
      if (normalizedInput.includes(keyword.toLowerCase())) {
        return item.response
      }
    }
  }
  
  return DEFAULT_RESPONSE
}
