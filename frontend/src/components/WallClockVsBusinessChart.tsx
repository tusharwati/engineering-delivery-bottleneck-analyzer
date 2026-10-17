import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { BottleneckPR } from '../types';

interface WallClockVsBusinessChartProps {
  bottlenecks: BottleneckPR[];
  slaHours: number;
}

export const WallClockVsBusinessChart: React.FC<WallClockVsBusinessChartProps> = ({
  bottlenecks,
  slaHours,
}) => {
  // Take top 8 waiting PRs for clear visualization
  const data = bottlenecks.slice(0, 8).map((pr) => ({
    name: pr.title.length > 28 ? pr.title.substring(0, 25) + '...' : pr.title,
    fullTitle: pr.title,
    calendar: pr.calendar_waiting_hours,
    business: pr.business_waiting_hours,
    saved: pr.non_working_hours,
    slaTarget: slaHours,
  }));

  if (data.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 text-center text-slate-400 text-sm">
        No active pull requests awaiting review to display.
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">
            Wall-Clock (Calendar) vs. Business-Hours Waiting Time
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Demonstrates non-working hours distortion filtered out per pull request
          </p>
        </div>
        <div className="text-xs font-mono px-2.5 py-1 rounded bg-sky-500/10 border border-sky-500/20 text-sky-300">
          SLA Target: {slaHours}h
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="name"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              interval={0}
              angle={-20}
              textAnchor="end"
            />
            <YAxis stroke="#64748b" fontSize={11} unit="h" tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.5rem',
                fontSize: '12px',
              }}
              formatter={(value: any, name: any) => [
                `${Number(value).toFixed(1)} hours`,
                name === 'calendar' ? 'Calendar Wall-Clock Wait' : 'Actual Business-Hours Wait',
              ]}
              labelFormatter={(label, payload) => {
                const item = payload?.[0]?.payload;
                return item ? item.fullTitle : label;
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
              formatter={(val) => (val === 'calendar' ? 'Calendar Wall-Clock Time' : 'Business Hours Time')}
            />
            <ReferenceLine
              y={slaHours}
              stroke="#ef4444"
              strokeDasharray="4 4"
              label={{ value: `SLA (${slaHours}h)`, fill: '#ef4444', fontSize: 10, position: 'right' }}
            />
            <Bar dataKey="calendar" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={14} opacity={0.7} />
            <Bar dataKey="business" fill="#10b981" radius={[4, 4, 0, 0]} barSize={14} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
