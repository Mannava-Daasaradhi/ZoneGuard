import { useState, useEffect } from 'react';
import { LOSS_RATIO_DATA, formatCurrency } from '../../data/chartMockData';
import { getLossRatioTrend } from '../../services/api';

interface CircularProgressProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
}

function CircularProgress({ percentage, size = 160, strokeWidth = 12 }: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  // Color based on percentage: emerald (<70%), amber (70-90%), red (>90%)
  const getColor = (pct: number) => {
    if (pct < 70) return { stroke: '#10b981', bg: 'rgba(16, 185, 129, 0.1)', text: 'text-emerald-400' };
    if (pct < 90) return { stroke: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', text: 'text-amber-400' };
    return { stroke: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)', text: 'text-red-400' };
  };

  const colors = getColor(percentage);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#334155"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
          style={{
            filter: `drop-shadow(0 0 8px ${colors.stroke}40)`,
          }}
        />
      </svg>
      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-bold ${colors.text}`}>
          {percentage.toFixed(1)}%
        </span>
        <span className="text-slate-400 text-xs mt-1">Loss Ratio</span>
      </div>
    </div>
  );
}

export default function LossRatioWidget() {
  const [liveData, setLiveData] = useState<{
    premiumsCollected: number;
    totalPayouts: number;
    lossRatio: number;
  } | null>(null);

  useEffect(() => {
    getLossRatioTrend()
      .then((trend) => {
        if (trend && trend.length > 0) {
          // Aggregate from trend data
          const totalPremiums = trend.reduce((s, d) => s + d.premiums, 0);
          const totalPayouts = trend.reduce((s, d) => s + d.payouts, 0);
          if (totalPremiums > 0) {
            setLiveData({
              premiumsCollected: totalPremiums,
              totalPayouts: totalPayouts,
              lossRatio: (totalPayouts / totalPremiums) * 100,
            });
          }
        }
      })
      .catch(() => {});
  }, []);

  const { premiumsCollected, totalPayouts, lossRatio } = liveData || LOSS_RATIO_DATA;

  // Determine status based on loss ratio
  const getStatus = (ratio: number) => {
    if (ratio < 70)
      return {
        label: 'Healthy',
        description: 'Loss ratio is within target range',
        color: 'text-emerald-400',
        bgColor: 'bg-emerald-500/10 border-emerald-500/30',
      };
    if (ratio < 90)
      return {
        label: 'Caution',
        description: 'Loss ratio approaching threshold',
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/10 border-amber-500/30',
      };
    return {
      label: 'Critical',
      description: 'Loss ratio exceeds target',
      color: 'text-red-400',
      bgColor: 'bg-red-500/10 border-red-500/30',
    };
  };

  const status = getStatus(lossRatio);
  const netPosition = premiumsCollected - totalPayouts;

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-white font-bold text-lg">Loss Ratio</h3>
          <p className="text-slate-400 text-xs">
            {liveData ? 'Live data from analytics' : 'Weekly performance snapshot'}
          </p>
        </div>
        <div className={`${status.bgColor} border rounded-lg px-2.5 py-1`}>
          <span className={`text-xs font-bold ${status.color}`}>{status.label}</span>
        </div>
      </div>

      {/* Circular Progress */}
      <div className="flex justify-center my-6">
        <CircularProgress percentage={lossRatio} />
      </div>

      {/* Status description */}
      <p className="text-center text-slate-400 text-xs mb-4">{status.description}</p>

      {/* Premium vs Payout breakdown */}
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <p className="text-slate-400 text-xs mb-1">Premiums Collected</p>
            <p className="text-emerald-400 font-bold text-lg">
              {formatCurrency(premiumsCollected)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-slate-400 text-xs mb-1">Total Payouts</p>
            <p className="text-amber-400 font-bold text-lg">
              {formatCurrency(totalPayouts)}
            </p>
          </div>
        </div>

        {/* Net position bar */}
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-xs">Net Position</span>
            <span
              className={`font-bold text-sm ${netPosition >= 0 ? 'text-emerald-400' : 'text-red-400'}`}
            >
              {netPosition >= 0 ? '+' : ''}
              {formatCurrency(netPosition)}
            </span>
          </div>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                netPosition >= 0 ? 'bg-emerald-500' : 'bg-red-500'
              }`}
              style={{
                width: `${Math.min(100, (Math.abs(netPosition) / Math.max(premiumsCollected, 1)) * 100)}%`,
              }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-slate-500 text-[10px]">0%</span>
            <span className="text-slate-500 text-[10px]">100%</span>
          </div>
        </div>
      </div>

      {/* Quick metrics */}
      <div className="grid grid-cols-3 gap-2 mt-4">
        <div className="bg-slate-900 rounded-lg p-2 text-center">
          <p className="text-slate-500 text-[10px]">Target</p>
          <p className="text-slate-300 text-xs font-medium">&lt;70%</p>
        </div>
        <div className="bg-slate-900 rounded-lg p-2 text-center">
          <p className="text-slate-500 text-[10px]">Current</p>
          <p className={`text-xs font-medium ${status.color}`}>{lossRatio.toFixed(1)}%</p>
        </div>
        <div className="bg-slate-900 rounded-lg p-2 text-center">
          <p className="text-slate-500 text-[10px]">Delta</p>
          <p
            className={`text-xs font-medium ${
              lossRatio < 70 ? 'text-emerald-400' : 'text-red-400'
            }`}
          >
            {lossRatio < 70 ? '-' : '+'}
            {Math.abs(lossRatio - 70).toFixed(1)}%
          </p>
        </div>
      </div>
    </div>
  );
}
