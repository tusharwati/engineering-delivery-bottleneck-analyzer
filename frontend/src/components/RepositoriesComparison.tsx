import React from 'react';
import { GitPullRequest, GitBranch, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { Repository } from '../types';

interface RepositoriesComparisonProps {
  repositories: Repository[];
}

export const RepositoriesComparison: React.FC<RepositoriesComparisonProps> = ({
  repositories,
}) => {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Repository Review Baselines & Queues</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Learned historical benchmarks (Median, P90) with sample sufficiency gating (N &ge; 10)
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {repositories.map((repo) => {
          const baseline = repo.baseline;
          const isSufficient = baseline?.status === 'SUFFICIENT_SAMPLE';

          return (
            <div
              key={repo.id}
              className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/60 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-200 truncate">
                    <GitBranch className="w-3.5 h-3.5 text-sky-400 flex-shrink-0" />
                    <span className="truncate">{repo.name}</span>
                  </div>
                  {isSufficient ? (
                    <span className="flex items-center gap-1 text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                      <CheckCircle2 className="w-2.5 h-2.5" />
                      <span>Learned</span>
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] font-medium text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                      <AlertCircle className="w-2.5 h-2.5" />
                      <span>Fallback SLA</span>
                    </span>
                  )}
                </div>

                <div className="text-xs text-slate-400 line-clamp-1 mb-3">
                  {repo.description || 'DevLake tracked repository'}
                </div>
              </div>

              <div className="space-y-2 border-t border-slate-700/50 pt-2 text-xs">
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-400 flex items-center gap-1">
                    <GitPullRequest className="w-3 h-3 text-sky-400" />
                    <span>Open PRs:</span>
                  </span>
                  <span className="font-semibold text-white">{repo.open_prs}</span>
                </div>

                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-emerald-400" />
                    <span>Median Pickup:</span>
                  </span>
                  <span className="font-mono text-emerald-300 font-semibold">
                    {baseline ? `${baseline.median_hours}h` : '—'}
                  </span>
                </div>

                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-purple-400" />
                    <span>P90 Pickup:</span>
                  </span>
                  <span className="font-mono text-purple-300 font-semibold">
                    {baseline ? `${baseline.p90_hours}h` : '—'}
                  </span>
                </div>

                <div className="text-[10px] text-slate-500 pt-1 text-right">
                  Sample: {baseline?.sample_count ?? 0} historical PRs
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
