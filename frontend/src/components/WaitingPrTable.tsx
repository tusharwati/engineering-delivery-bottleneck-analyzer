import React from 'react';
import { AlertCircle, Clock, Info, ShieldAlert, Sparkles, User, GitCommit } from 'lucide-react';
import { BottleneckPR } from '../types';

interface WaitingPrTableProps {
  bottlenecks: BottleneckPR[];
  onSelectPr: (pr: BottleneckPR) => void;
}

export const WaitingPrTable: React.FC<WaitingPrTableProps> = ({
  bottlenecks,
  onSelectPr,
}) => {
  const getPriorityBadge = (level: string, score: number) => {
    switch (level) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
            <ShieldAlert className="w-3 h-3 text-rose-400" />
            <span>{score} Critical</span>
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
            <AlertCircle className="w-3 h-3 text-amber-400" />
            <span>{score} High</span>
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/15 text-sky-300 border border-sky-500/30">
            <span>{score} Medium</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <span>{score} Low</span>
          </span>
        );
    }
  };

  const getSlaBadge = (status: string, ratio: number) => {
    switch (status) {
      case 'BREACHED':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-950/60 text-rose-300 border border-rose-800">
            Breached ({Math.round(ratio * 100)}%)
          </span>
        );
      case 'AT_RISK':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-950/60 text-amber-300 border border-amber-800">
            At Risk ({Math.round(ratio * 100)}%)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-800">
            Healthy ({Math.round(ratio * 100)}%)
          </span>
        );
    }
  };

  if (bottlenecks.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-10 text-center">
        <Sparkles className="w-8 h-8 text-emerald-400 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-slate-100">Zero Review Bottlenecks</h4>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          No open pull requests are currently exceeding review SLAs or matching your filter criteria.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">
            Prioritized Unreviewed Pull Request Queue
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Ranked by multi-factor explainable urgency score (SLA ratio, baseline deviation, diff size, queue load)
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Showing {bottlenecks.length} PRs
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-800/60 text-slate-400 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Urgency Priority</th>
              <th className="py-3 px-4">Pull Request</th>
              <th className="py-3 px-4">Repository</th>
              <th className="py-3 px-4">Author</th>
              <th className="py-3 px-4">Business Wait</th>
              <th className="py-3 px-4">Calendar Wait</th>
              <th className="py-3 px-4">SLA Status</th>
              <th className="py-3 px-4">Diff Size</th>
              <th className="py-3 px-4 text-right">Rationale</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {bottlenecks.map((pr) => (
              <tr
                key={pr.id}
                className="hover:bg-slate-800/30 transition group"
              >
                <td className="py-3 px-4 whitespace-nowrap">
                  {getPriorityBadge(pr.priority_level, pr.priority_score)}
                </td>
                <td className="py-3 px-4 max-w-xs">
                  <div className="flex items-center gap-1.5">
                    {pr.is_draft && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        Draft
                      </span>
                    )}
                    {pr.is_bot_filtered && (
                      <span 
                        title="Automated bot comments were excluded from review pickup" 
                        className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20"
                      >
                        Bot Filtered
                      </span>
                    )}
                    <span className="font-medium text-slate-100 truncate block group-hover:text-sky-300 transition">
                      {pr.title}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4 whitespace-nowrap text-slate-300">
                  <span className="font-mono text-[11px]">{pr.repo_name}</span>
                </td>
                <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                  <div className="flex items-center gap-1">
                    <User className="w-3 h-3 text-slate-500" />
                    <span>{pr.author_name}</span>
                  </div>
                </td>
                <td className="py-3 px-4 whitespace-nowrap font-mono font-semibold text-emerald-400">
                  {pr.business_waiting_hours.toFixed(1)}h
                </td>
                <td className="py-3 px-4 whitespace-nowrap font-mono text-slate-400">
                  {pr.calendar_waiting_hours.toFixed(1)}h
                  {pr.non_working_hours > 0 && (
                    <span className="text-[10px] text-slate-500 ml-1">
                      (-{pr.non_working_hours.toFixed(0)}h off)
                    </span>
                  )}
                </td>
                <td className="py-3 px-4 whitespace-nowrap">
                  {getSlaBadge(pr.sla_status, pr.sla_ratio)}
                </td>
                <td className="py-3 px-4 whitespace-nowrap font-mono text-[11px]">
                  <span className="text-emerald-400">+{pr.additions}</span>
                  <span className="text-slate-500 mx-0.5">/</span>
                  <span className="text-rose-400">-{pr.deletions}</span>
                </td>
                <td className="py-3 px-4 whitespace-nowrap text-right">
                  <button
                    onClick={() => onSelectPr(pr)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-sky-400 border border-slate-700 text-xs font-medium transition"
                  >
                    <Info className="w-3 h-3" />
                    <span>Explain</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
