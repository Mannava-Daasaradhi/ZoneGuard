export type RiskTier = 'low' | 'medium' | 'high' | 'flood-prone';
export type SignalStatus = 'active' | 'inactive' | 'firing';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'NOISE';
export type DayStatus = 'normal' | 'disrupted' | 'payout';

export interface Zone {
  id: string;
  name: string;
  pinCode: string;
  pin_code?: string;
  lat?: number;
  lng?: number;
  riskTier: RiskTier;
  risk_tier?: string;
  riskScore: number;
  risk_score?: number;
  weeklyPremium: number;
  weekly_premium?: number;
  maxWeeklyPayout: number;
  max_weekly_payout?: number;
  activeRiders: number;
  active_riders?: number;
  disruptions: number;
  historical_disruptions?: number;
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
  zone_id?: string;
  rider_id?: string;
  date: string;
  confidence: ConfidenceLevel;
  signals: number;
  recommendedPayout: number;
  recommended_payout?: number;
  auditSummary: string;
  status: 'pending' | 'pending_review' | 'approved' | 'rejected' | 'held';
  exclusion_check?: ExclusionCheck;
  fraud_score?: number;
}

export interface KPI {
  label: string;
  value: string;
  delta: string;
  trend: 'up' | 'down' | 'stable';
  sparkline: number[];
}

// Phase 2 types

export interface Exclusion {
  id: string;
  name: string;
  description: string;
  category: 'standard' | 'operational' | 'behavioral';
  check_phase: string;
}

export interface ExclusionCheck {
  passed: boolean;
  exclusions_evaluated: string[];
  exclusions_triggered: { id: string; name: string; reason: string }[];
}

export interface PolicyData {
  id: string;
  rider_id: string;
  zone_id: string;
  status: 'active' | 'expired' | 'cancelled';
  weekly_premium: number;
  max_payout: number;
  coverage_start: string;
  coverage_end: string;
  is_forward_locked: boolean;
  forward_lock_weeks: number;
  created_at: string;
  exclusions?: Exclusion[];
}

export interface PremiumBreakdown {
  risk_score: number;
  premium: number;
  tier: string;
  max_payout: number;
  factor_breakdown: Record<string, {
    weight: number;
    raw_score: number;
    contribution: number;
    contribution_inr: number;
  }>;
}

export interface SimulationResult {
  simulation_id: string;
  scenario: string;
  zone: { id: string; name: string };
  disruption_event_id: string;
  fusion: any;
  zone_twin: any;
  claims_created: number;
  claims: any[];
  payouts_created: number;
  payouts: any[];
  signals: any;
}

export interface ZoneSignalData {
  zone_id: string;
  zone_name: string;
  s1_environmental: { status: string; value: string; threshold: string; raw?: any };
  s2_mobility: { status: string; value: string; threshold: string; raw?: any };
  s3_economic: { status: string; value: string; threshold: string; raw?: any };
  s4_crowd: { status: string; value: string; threshold: string; raw?: any };
  confidence: ConfidenceLevel;
  signals_fired: number;
  is_disrupted: boolean;
  fusion?: any;
  weather?: any;
}
