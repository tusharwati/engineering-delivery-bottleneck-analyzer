import React from 'react';
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
import { BacklogTrendItem } from '../types';

interface BacklogChartProps {
  trend: BacklogTrendItem[];
}

export const BacklogChart: React.FC<BacklogChartProps> = ({ trend }) => {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Review Queue Backlog Trend</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Daily PR arrivals vs. reviews/merges with cumulative queue estimate
          </p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={trend} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
            <defs>
              <linearGradient id="backlogGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0284c7" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#0284c7" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.5rem',
                fontSize: '12px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
            <Area
              type="monotone"
              dataKey="backlog_estimate"
              name="Active Backlog Queue"
              stroke="#0284c7"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#backlogGrad)"
            />
            <Area
              type="monotone"
              dataKey="opened"
              name="Opened PRs"
              stroke="#a855f7"
              strokeWidth={1.5}
              fill="transparent"
            />
            <Area
              type="monotone"
              dataKey="merged"
              name="Merged PRs"
              stroke="#10b981"
              strokeWidth={1.5}
              fill="transparent"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
