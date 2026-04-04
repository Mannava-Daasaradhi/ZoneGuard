import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { PAYOUT_CHART_DATA, getPayoutTotal, formatCurrency } from '../../data/chartMockData';

interface TooltipPayload {
  value: number;
  payload: {
    day: string;
    date: string;
    amount: number;
  };
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
}

const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl">
      <p className="text-white font-semibold text-sm mb-1">{data.day}</p>
      <p className="text-slate-400 text-xs mb-2">{data.date}</p>
      <div className="flex items-center gap-2">
        <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
        <span className="text-white font-bold text-lg">
          ₹{data.amount.toLocaleString('en-IN')}
        </span>
      </div>
    </div>
  );
};

export default function PayoutChart() {
  const totalPayout = getPayoutTotal();
  const avgDaily = Math.round(totalPayout / 7);

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-white font-bold text-lg">Daily Payouts</h3>
          <p className="text-slate-400 text-xs">
            Last 7 days · {formatCurrency(totalPayout)} total · {formatCurrency(avgDaily)}/day avg
          </p>
        </div>
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-3 py-1.5">
          <p className="text-emerald-400 text-xs font-medium">
            Week Total: <span className="font-bold">{formatCurrency(totalPayout)}</span>
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={PAYOUT_CHART_DATA}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="payoutGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={1} />
                <stop offset="100%" stopColor="#047857" stopOpacity={1} />
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
              tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1e293b' }} />
            <Bar
              dataKey="amount"
              radius={[4, 4, 0, 0]}
              maxBarSize={48}
            >
              {PAYOUT_CHART_DATA.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill="url(#payoutGradient)"
                  className="hover:opacity-80 transition-opacity"
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Daily breakdown mini-stats */}
      <div className="grid grid-cols-7 gap-1 mt-4 pt-4 border-t border-slate-700">
        {PAYOUT_CHART_DATA.map((day) => (
          <div key={day.day} className="text-center">
            <p className="text-slate-500 text-[10px]">{day.day}</p>
            <p className="text-slate-300 text-xs font-medium">
              {formatCurrency(day.amount)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
