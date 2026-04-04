// Chart mock data for Admin Dashboard analytics

export interface DailyClaimsData {
  day: string;
  date: string;
  approved: number;
  pending: number;
  rejected: number;
  total: number;
}

export interface DailyPayoutData {
  day: string;
  date: string;
  amount: number;
}

export interface LossRatioData {
  premiumsCollected: number;
  totalPayouts: number;
  lossRatio: number;
}

// Last 7 days of claims data (Mon-Sun)
export const CLAIMS_CHART_DATA: DailyClaimsData[] = [
  { day: 'Mon', date: '2026-03-16', approved: 4, pending: 2, rejected: 1, total: 7 },
  { day: 'Tue', date: '2026-03-17', approved: 6, pending: 3, rejected: 2, total: 11 },
  { day: 'Wed', date: '2026-03-18', approved: 8, pending: 4, rejected: 3, total: 15 },
  { day: 'Thu', date: '2026-03-19', approved: 5, pending: 3, rejected: 1, total: 9 },
  { day: 'Fri', date: '2026-03-20', approved: 7, pending: 2, rejected: 2, total: 11 },
  { day: 'Sat', date: '2026-03-21', approved: 3, pending: 1, rejected: 1, total: 5 },
  { day: 'Sun', date: '2026-03-22', approved: 5, pending: 2, rejected: 1, total: 8 },
];

// Last 7 days of payout data (₹5000-₹25000/day)
export const PAYOUT_CHART_DATA: DailyPayoutData[] = [
  { day: 'Mon', date: '2026-03-16', amount: 8500 },
  { day: 'Tue', date: '2026-03-17', amount: 14200 },
  { day: 'Wed', date: '2026-03-18', amount: 22800 },
  { day: 'Thu', date: '2026-03-19', amount: 12500 },
  { day: 'Fri', date: '2026-03-20', amount: 18600 },
  { day: 'Sat', date: '2026-03-21', amount: 6800 },
  { day: 'Sun', date: '2026-03-22', amount: 11200 },
];

// Loss ratio data
export const LOSS_RATIO_DATA: LossRatioData = {
  premiumsCollected: 45000,
  totalPayouts: 32000,
  lossRatio: 71.1, // (32000 / 45000) * 100
};

// Helper function to format currency
export const formatCurrency = (amount: number): string => {
  if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(1)}L`;
  }
  if (amount >= 1000) {
    return `₹${(amount / 1000).toFixed(1)}K`;
  }
  return `₹${amount.toLocaleString('en-IN')}`;
};

// Calculate totals for display
export const getClaimsTotals = () => {
  return CLAIMS_CHART_DATA.reduce(
    (acc, day) => ({
      approved: acc.approved + day.approved,
      pending: acc.pending + day.pending,
      rejected: acc.rejected + day.rejected,
      total: acc.total + day.total,
    }),
    { approved: 0, pending: 0, rejected: 0, total: 0 }
  );
};

export const getPayoutTotal = () => {
  return PAYOUT_CHART_DATA.reduce((sum, day) => sum + day.amount, 0);
};
