import { Zone, WeekDay, Payout, Signal, ClaimEvent, KPI } from '../types';

export const ZONES: Zone[] = [
  { id: 'hsr', name: 'HSR Layout', pinCode: '560102', riskTier: 'medium', riskScore: 58, weeklyPremium: 49, maxWeeklyPayout: 2200, activeRiders: 142, disruptions: 3 },
  { id: 'koramangala', name: 'Koramangala', pinCode: '560034', riskTier: 'medium', riskScore: 54, weeklyPremium: 49, maxWeeklyPayout: 2200, activeRiders: 198, disruptions: 3 },
  { id: 'whitefield', name: 'Whitefield', pinCode: '560066', riskTier: 'low', riskScore: 22, weeklyPremium: 29, maxWeeklyPayout: 1800, activeRiders: 215, disruptions: 1 },
  { id: 'indiranagar', name: 'Indiranagar', pinCode: '560038', riskTier: 'medium', riskScore: 61, weeklyPremium: 49, maxWeeklyPayout: 2200, activeRiders: 167, disruptions: 3 },
  { id: 'electronic-city', name: 'Electronic City', pinCode: '560100', riskTier: 'low', riskScore: 31, weeklyPremium: 29, maxWeeklyPayout: 1800, activeRiders: 289, disruptions: 1 },
  { id: 'bellandur', name: 'Bellandur', pinCode: '560103', riskTier: 'flood-prone', riskScore: 87, weeklyPremium: 99, maxWeeklyPayout: 3500, activeRiders: 94, disruptions: 8 },
  { id: 'btm-layout', name: 'BTM Layout', pinCode: '560076', riskTier: 'high', riskScore: 72, weeklyPremium: 69, maxWeeklyPayout: 2800, activeRiders: 131, disruptions: 5 },
  { id: 'jp-nagar', name: 'JP Nagar', pinCode: '560078', riskTier: 'high', riskScore: 68, weeklyPremium: 69, maxWeeklyPayout: 2800, activeRiders: 112, disruptions: 5 },
  { id: 'yelahanka', name: 'Yelahanka', pinCode: '560064', riskTier: 'low', riskScore: 19, weeklyPremium: 29, maxWeeklyPayout: 1800, activeRiders: 178, disruptions: 1 },
  { id: 'hebbal', name: 'Hebbal', pinCode: '560024', riskTier: 'high', riskScore: 74, weeklyPremium: 69, maxWeeklyPayout: 2800, activeRiders: 103, disruptions: 5 },
];

export const RAVI_WEEK: WeekDay[] = [
  { day: 'Mon', date: '2026-03-16', status: 'normal', earnings: 2600 },
  { day: 'Tue', date: '2026-03-17', status: 'normal', earnings: 2800 },
  { day: 'Wed', date: '2026-03-18', status: 'payout', earnings: 0, payoutAmount: 1950, disruptionType: 'Flash flood — all 4 signals fired' },
  { day: 'Thu', date: '2026-03-19', status: 'payout', earnings: 0, payoutAmount: 1950, disruptionType: 'Flood continues — signals sustained' },
  { day: 'Fri', date: '2026-03-20', status: 'normal', earnings: 2400 },
  { day: 'Sat', date: '2026-03-21', status: 'normal', earnings: 2200 },
  { day: 'Sun', date: '2026-03-22', status: 'normal', earnings: 0 },
];

export const PAYOUTS: Payout[] = [
  { id: 'P001', date: '2026-03-19', amount: 1950, zone: 'HSR Layout', trigger: 'Flash Flood (ENV-01)', confidence: 'HIGH', upiRef: 'ZG-2026-3819' },
  { id: 'P002', date: '2026-03-18', amount: 1950, zone: 'HSR Layout', trigger: 'Flash Flood (ENV-01)', confidence: 'HIGH', upiRef: 'ZG-2026-3818' },
  { id: 'P003', date: '2026-02-11', amount: 1950, zone: 'HSR Layout', trigger: 'Transport Strike (SOC-02)', confidence: 'HIGH', upiRef: 'ZG-2026-2111' },
  { id: 'P004', date: '2026-01-08', amount: 1650, zone: 'HSR Layout', trigger: 'Severe AQI (ENV-02)', confidence: 'MEDIUM', upiRef: 'ZG-2026-0801' },
];

export const QUAD_SIGNALS: Signal[] = [
  { id: 'S1', name: 'Environmental', description: 'OpenWeatherMap + NDMA', status: 'inactive', value: 'Rainfall: 12mm/hr', threshold: '>65mm/hr' },
  { id: 'S2', name: 'Mobility', description: 'OSRM Zone Index', status: 'inactive', value: 'Mobility: 94% of baseline', threshold: '<25% of baseline' },
  { id: 'S3', name: 'Economic', description: 'Order Volume Proxy', status: 'inactive', value: 'Orders: 98% of baseline', threshold: '<30% of baseline' },
  { id: 'S4', name: 'Crowd', description: 'WhatsApp Check-ins', status: 'inactive', value: 'Check-ins: 3% inactivity', threshold: '≥40% inactivity' },
];

export const CLAIMS_QUEUE: ClaimEvent[] = [
  {
    id: 'CE-001', zone: 'BTM Layout', date: '2026-03-19', confidence: 'MEDIUM', signals: 3,
    recommendedPayout: 2100, status: 'pending',
    auditSummary: 'Signals S1, S2, S3 converged at 14:32 IST. S4 check-in response rate was 31% (threshold 40%) — below threshold but trending upward. Rainfall measured at 58mm/hr against 65mm/hr threshold. Mobility index dropped to 28% of baseline. Historical comparison: 3 similar events in BTM Layout over 24 months all qualified. Recommendation: APPROVE with 90-minute recheck on S4.',
  },
  {
    id: 'CE-002', zone: 'Hebbal', date: '2026-03-18', confidence: 'MEDIUM', signals: 3,
    recommendedPayout: 1800, status: 'pending',
    auditSummary: 'Signals S1, S3, S4 converged. S2 (mobility) showed 34% baseline drop — below 75% threshold. Fog event consistent with IMD winter forecast. 47 of 103 registered riders confirmed inactivity (46%). Order volume at 22% of baseline. ZoneTwin counterfactual: fog events of this severity historically produce 38–52% rider inactivity. Pattern consistent. Recommendation: APPROVE.',
  },
  {
    id: 'CE-003', zone: 'JP Nagar', date: '2026-03-17', confidence: 'MEDIUM', signals: 3,
    recommendedPayout: 2100, status: 'approved',
    auditSummary: 'All thresholds near-boundary. Approved after 1-hour recheck confirmed S2 dropped to 22%. Payout disbursed.',
  },
];

export const KPIS: KPI[] = [
  { label: 'Loss Ratio', value: '54.2%', delta: '-2.1%', trend: 'down', sparkline: [58, 57, 61, 55, 56, 54, 54] },
  { label: 'Active Policies', value: '1,624', delta: '+47', trend: 'up', sparkline: [1420, 1490, 1530, 1558, 1580, 1601, 1624] },
  { label: 'Payouts This Week', value: '₹3.8L', delta: '+₹1.2L', trend: 'up', sparkline: [18000, 22000, 19000, 31000, 28000, 38000, 38000] },
  { label: 'Zones at Risk', value: '3', delta: '+1', trend: 'up', sparkline: [1, 2, 1, 2, 3, 3, 3] },
];

export const RIDER = {
  name: 'Ravi Kumar',
  riderId: 'AMZFLEX-BLR-04821',
  zone: ZONES[0],
  weeklyEarningsBaseline: 2600,
  tenureWeeks: 28,
  coverageActive: true,
  premiumPaidThisWeek: true,
};
