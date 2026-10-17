import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  badge?: string;
  variant?: 'default' | 'danger' | 'warning' | 'success';
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  badge,
  variant = 'default',
}) => {
  const variantStyles = {
    default: 'border-slate-800 bg-slate-900/60 text-slate-100',
    danger: 'border-rose-500/30 bg-rose-500/5 text-rose-200',
    warning: 'border-amber-500/30 bg-amber-500/5 text-amber-200',
    success: 'border-emerald-500/30 bg-emerald-500/5 text-emerald-200',
  };

  const iconColors = {
    default: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
    danger: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
    warning: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    success: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  };

  return (
    <div className={`p-5 rounded-xl border backdrop-blur transition hover:border-slate-700 ${variantStyles[variant]}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
        <div className={`p-2 rounded-lg border ${iconColors[variant]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white">{value}</span>
        {badge && (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
            {badge}
          </span>
        )}
      </div>
      {subtext && <p className="text-xs text-slate-400 mt-2">{subtext}</p>}
    </div>
  );
};
