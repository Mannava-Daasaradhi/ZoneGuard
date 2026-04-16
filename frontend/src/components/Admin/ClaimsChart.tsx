import { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { CLAIMS_CHART_DATA, getClaimsTotals } from '../../data/chartMockData';
import { getClaimsByZone } from '../../services/api';

interface TooltipPayload {
  dataKey: string;
  value: number;
  color: string;
  name: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload || payload.length === 0) return null;

  const total = payload.reduce((sum, entry) => sum + entry.value, 0);

  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl">
      <p className="text-white font-semibold text-sm mb-2">{label}</p>
      <div className="space-y-1">
        {payload.map((entry) => (
          <div key={entry.dataKey} className="flex items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-slate-300 capitalize">{entry.name}</span>
            </div>
            <span className="text-white font-medium">{entry.value}</span>
          </div>
        ))}
        <div className="pt-1 mt-1 border-t border-slate-600 flex items-center justify-between text-xs">
          <span className="text-slate-400">Total</span>
          <span className="text-white font-bold">{total}</span>
        </div>
      </div>
    </div>
  );
};

interface ZoneClaimData {
  zone_id: string;
  zone_name: string;
  total_claims: number;
  approved: number;
  rejected: number;
  pending: number;
}

export default function ClaimsChart() {
  const [zoneData, setZoneData] = useState<ZoneClaimData[] | null>(null);
  const [useApi, setUseApi] = useState(true);

  useEffect(() => {
    getClaimsByZone()
      .then((data) => {
        if (data && data.length > 0) {
          setZoneData(data);
        } else {
          setUseApi(false);
        }
      })
      .catch(() => setUseApi(false));
  }, []);

  // Build chart data from API or mock
  const chartData = useApi && zoneData
    ? zoneData.map((z) => ({
        day: z.zone_name.slice(0, 8),
        date: z.zone_id,
        approved: z.approved,
        pending: z.pending,
        rejected: z.rejected,
        total: z.total_claims,
      }))
    : CLAIMS_CHART_DATA;

  const totals = useApi && zoneData
    ? zoneData.reduce(
        (acc, z) => ({
          approved: acc.approved + z.approved,
          pending: acc.pending + z.pending,
          rejected: acc.rejected + z.rejected,
          total: acc.total + z.total_claims,
        }),
        { approved: 0, pending: 0, rejected: 0, total: 0 }
      )
    : getClaimsTotals();

  const subtitle = useApi && zoneData ? `By zone · ${totals.total} total claims` : `Last 7 days · ${totals.total} total claims`;

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-white font-bold text-lg">Claims Overview</h3>
          <p className="text-slate-400 text-xs">{subtitle}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-slate-400 text-xs">{totals.approved} approved</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span className="text-slate-400 text-xs">{totals.pending} pending</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <span className="text-slate-400 text-xs">{totals.rejected} rejected</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="approvedGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="pendingGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="rejectedGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 12 }}
              dy={8}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 12 }}
              dx={-8}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: '16px' }}
              formatter={(value: string) => (
                <span className="text-slate-400 text-xs capitalize">{value}</span>
              )}
            />
            <Area
              type="monotone"
              dataKey="approved"
              name="Approved"
              stackId="1"
              stroke="#10b981"
              strokeWidth={2}
              fill="url(#approvedGradient)"
            />
            <Area
              type="monotone"
              dataKey="pending"
              name="Pending"
              stackId="1"
              stroke="#f59e0b"
              strokeWidth={2}
              fill="url(#pendingGradient)"
            />
            <Area
              type="monotone"
              dataKey="rejected"
              name="Rejected"
              stackId="1"
              stroke="#ef4444"
              strokeWidth={2}
              fill="url(#rejectedGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
