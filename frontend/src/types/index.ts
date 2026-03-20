export type RiskTier = 'low' | 'medium' | 'high' | 'flood-prone';
export type SignalStatus = 'active' | 'inactive' | 'firing';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'NOISE';
export type DayStatus = 'normal' | 'disrupted' | 'payout';

export interface Zone {
  id: string;
  name: string;
  pinCode: string;
  riskTier: RiskTier;
  riskScore: number;
  weeklyPremium: number;
  maxWeeklyPayout: number;
  activeRiders: number;
  disruptions: number;
}

export interface WeekDay {
  day: string;
  date: string;
  status: DayStatus;
  earnings: number;
  payoutAmount?: number;
  disruptionType?: string;
}

export interface Payout {
  id: string;
  date: string;
  amount: number;
  zone: string;
  trigger: string;
  confidence: ConfidenceLevel;
  upiRef: string;
}

export interface Signal {
  id: 'S1' | 'S2' | 'S3' | 'S4';
  name: string;
  description: string;
  status: SignalStatus;
  value: string;
  threshold: string;
  firedAt?: string;
}

export interface ClaimEvent {
  id: string;
  zone: string;
  date: string;
  confidence: ConfidenceLevel;
  signals: number;
  recommendedPayout: number;
  auditSummary: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface KPI {
  label: string;
  value: string;
  delta: string;
  trend: 'up' | 'down' | 'stable';
  sparkline: number[];
}
