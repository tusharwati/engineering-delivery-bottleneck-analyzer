import React from 'react';
import { Filter, RefreshCw } from 'lucide-react';
import { Repository } from '../types';

interface FilterBarProps {
  repositories: Repository[];
  selectedRepo: string;
  setSelectedRepo: (id: string) => void;
  selectedStatus: string;
  setSelectedStatus: (status: string) => void;
  minPriority: number;
  setMinPriority: (p: number) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  repositories,
  selectedRepo,
  setSelectedRepo,
  selectedStatus,
  setSelectedStatus,
  minPriority,
  setMinPriority,
  onRefresh,
  isLoading,
}) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
          <Filter className="w-3.5 h-3.5 text-sky-400" />
          <span>Filters:</span>
        </div>

        {/* Repository Filter */}
        <select
          value={selectedRepo}
          onChange={(e) => setSelectedRepo(e.target.value)}
          className="bg-slate-800/80 border border-slate-700 rounded-lg text-xs font-medium text-slate-200 px-3 py-1.5 focus:outline-none focus:border-sky-500"
        >
          <option value="all">All Repositories ({repositories.length})</option>
          {repositories.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>

        {/* SLA Status Filter */}
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="bg-slate-800/80 border border-slate-700 rounded-lg text-xs font-medium text-slate-200 px-3 py-1.5 focus:outline-none focus:border-sky-500"
        >
          <option value="">All SLA Statuses</option>
          <option value="BREACHED">Breached (&gt; 8h)</option>
          <option value="AT_RISK">At Risk (6h - 8h)</option>
          <option value="HEALTHY">Healthy (&lt; 6h)</option>
        </select>

        {/* Priority Filter */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800 text-xs text-slate-400">
          <span>Min Priority:</span>
          <select
            value={minPriority}
            onChange={(e) => setMinPriority(Number(e.target.value))}
            className="bg-slate-800/80 border border-slate-700 rounded-lg text-xs font-medium text-slate-200 px-2 py-1.5 focus:outline-none focus:border-sky-500"
          >
            <option value="0">Any (0+)</option>
            <option value="25">Medium (25+)</option>
            <option value="50">High (50+)</option>
            <option value="75">Critical (75+)</option>
          </select>
        </div>
      </div>

      <button
        onClick={onRefresh}
        disabled={isLoading}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition disabled:opacity-50"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-sky-400' : 'text-slate-400'}`} />
        <span>Refresh</span>
      </button>
    </div>
  );
};
