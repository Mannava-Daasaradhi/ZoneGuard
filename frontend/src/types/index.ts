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

export interface FusionResult {
  signals_fired: number;
  confidence: string;
  signal_details: Record<string, { breached: boolean; value: number; threshold: number; reason: string; details: Record<string, unknown> }>;
  should_auto_payout: boolean;
  should_recheck: boolean;
  needs_review: boolean;
  timestamp: string;
}

export interface ZoneTwinResult {
  zone_id: string;
  conditions: Record<string, number>;
  expected_inactivity: { p10: number; p50: number; p90: number };
  historical_baseline: Record<string, unknown>;
  interpretation: string;
}

export interface SimulationClaim {
  id: string;
  rider_id: string;
  status: string;
  recommended_payout: number;
  fraud_score: number;
  exclusion_check: ExclusionCheck;
}

export interface SimulationPayout {
  id: string | null;
  rider_id: string;
  amount: number;
  upi_ref: string;
  status: string;
}

export interface RawRider {
  id: string;
  name: string;
  zone_id?: string;
  weekly_earnings_baseline?: number;
  tenure_weeks?: number;
  phone?: string;
  kyc_verified?: boolean;
  upi_id?: string;
}

export interface RawApiZone {
  id: string;
  name: string;
  lat?: number;
  lng?: number;
  risk_score?: number;
  riskScore?: number;
  risk_tier?: string;
  riskTier?: string;
  active_riders?: number;
  activeRiders?: number;
  weekly_premium?: number;
  weeklyPremium?: number;
  pin_code?: string;
  pinCode?: string;
  max_weekly_payout?: number;
  maxWeeklyPayout?: number;
  historical_disruptions?: number;
  disruptions?: number;
}

export interface RawApiClaim {
  id: string;
  zone?: string;
  zone_id?: string;
  rider_id?: string;
  date?: string;
  created_at?: string;
  confidence?: string;
  recommendedPayout?: number;
  recommended_payout?: number;
  status: string;
  exclusion_check?: ExclusionCheck;
  fraud_score?: number;
  auditSummary?: string;
  signals?: number;
}

export interface RawApiPayout {
  id: string;
  created_at?: string;
  amount: number;
  upi_ref?: string;
  rider_id?: string;
  status?: string;
}

export interface ZoneSignalData {
  zone_id: string;
  zone_name: string;
  s1_environmental: { status: string; value: string; threshold: string; raw?: Record<string, unknown> };
  s2_mobility: { status: string; value: string; threshold: string; raw?: Record<string, unknown> };
  s3_economic: { status: string; value: string; threshold: string; raw?: Record<string, unknown> };
  s4_crowd: { status: string; value: string; threshold: string; raw?: Record<string, unknown> };
  confidence: ConfidenceLevel;
  signals_fired: number;
  is_disrupted: boolean;
  fusion?: FusionResult;
  weather?: Record<string, unknown>;
}

export interface SimulationResult {
  simulation_id: string;
  scenario: string;
  zone: { id: string; name: string };
  disruption_event_id: string;
  fusion: FusionResult;
  zone_twin: ZoneTwinResult;
  claims_created: number;
  claims: SimulationClaim[];
  payouts_created: number;
  payouts: SimulationPayout[];
  signals: ZoneSignalData;
}

// Phase 3 types

export interface EShramVerificationResponse {
  rider_id: string;
  eshram_id: string;
  eshram_verified: boolean;
  eshram_income_verified: boolean;
  income_match?: 'match' | 'deviation_minor' | 'deviation_major' | null;
  income_deviation_pct?: number | null;
  message: string;
  verified_at?: string | null;
}

export interface FederatedRoundSummary {
  round: number;
  participating_cities: string[];
  n_clients: number;
  total_training_samples: number;
  global_weight_norm: number;
  elapsed_seconds: number;
  status: string;
}

export interface FederatedRoundResult {
  status: string;
  federated_training: {
    rounds_completed: number;
    round_summaries: FederatedRoundSummary[];
    final_weight_norm: number;
    total_samples_across_clients: number;
    cities: string[];
    architecture: {
      algorithm: string;
      base_model: string;
      n_estimators: number;
      contamination: number;
      privacy_guarantee: string;
      production_transport: string;
      demo_mode: string;
    };
  };
  timestamp: string;
}

export interface RingAnalysis {
  zone_id: string;
  claim_count: number;
  verdict: 'genuine' | 'suspicious' | 'ring_detected' | 'insufficient_data';
  confidence: number;
  ring_signals: string[];
  inter_arrival: {
    mean_gap_seconds?: number;
    std_gap_seconds?: number;
    min_gap_seconds?: number;
    cv?: number;
  };
  clustering_coefficient: number;
  spike: {
    max_spike_count: number;
    spike_detected: boolean;
    spike_window_minutes: number;
    spike_threshold: number;
  };
  poisson_z_score?: number | null;
  recommendation: string;
}

export interface RingDetectionDemoResult {
  demo: string;
  genuine_disruption: {
    description: string;
    analysis: RingAnalysis;
  };
  coordinated_ring: {
    description: string;
    analysis: RingAnalysis;
  };
  takeaway: string;
}
