import React from 'react';
import { Zap, CheckCircle2, AlertOctagon, Bot, Clock, ShieldCheck } from 'lucide-react';
import { ComparativeEvaluation } from '../types';

interface EvaluationViewProps {
  evaluation: ComparativeEvaluation | null;
}

export const EvaluationView: React.FC<EvaluationViewProps> = ({ evaluation }) => {
  if (!evaluation) {
    return (
      <div className="p-8 text-center text-slate-400 text-xs">
        Loading comparative evaluation benchmark...
      </div>
    );
  }

  const { naive_wall_clock, business_hours_aware, distortion_analysis, false_positive_examples } = evaluation;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Benchmark Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">Empirical Evaluation: Wall-Clock vs. Business-Hours</h2>
            <p className="text-xs text-slate-400">
              Quantitative comparison measured across {evaluation.dataset_size} pull requests against {evaluation.configured_sla_target_hours}h SLA target
            </p>
          </div>
        </div>

        {/* Distortion Elimination Summary Banner */}
        <div className="mt-5 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-6 h-6 text-emerald-400 flex-shrink-0" />
            <div>
              <span className="text-sm font-bold text-emerald-200 block">
                {distortion_analysis.false_positive_alerts_eliminated} False Positive SLA Alerts Eliminated
              </span>
              <span className="text-xs text-emerald-300/80">
                Reduced noise by {distortion_analysis.false_alert_reduction_pct}% while uncovering bot-masked delays
              </span>
            </div>
          </div>
          <div className="flex items-center gap-6 font-mono text-xs">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Off-Hours Filtered</span>
              <span className="text-white font-bold">{distortion_analysis.total_non_working_hours_filtered.toFixed(0)} hours</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Bot Pickups Unmasked</span>
              <span className="text-emerald-400 font-bold">{distortion_analysis.bot_comments_filtered_count} PRs</span>
            </div>
          </div>
        </div>
      </div>

      {/* Side-by-Side Model Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Model A: Naive Wall-Clock */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-rose-500/30 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-400 uppercase tracking-wider">Baseline 1: Naive Wall-Clock SLA</span>
            <span className="text-xs px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 font-mono">Unadjusted</span>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-800/40">
              <span className="text-slate-400">Total Flagged SLA Breaches:</span>
              <span className="font-mono font-bold text-rose-400 text-sm">{naive_wall_clock.total_breaches} PRs ({naive_wall_clock.breach_rate_pct}%)</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-800/40">
              <span className="text-slate-400">Reported Mean Waiting Time:</span>
              <span className="font-mono text-slate-200">{naive_wall_clock.mean_waiting_hours.toFixed(1)} hours</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-800/40">
              <span className="text-slate-400">Reported Median Waiting Time:</span>
              <span className="font-mono text-slate-200">{naive_wall_clock.median_waiting_hours.toFixed(1)} hours</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-800/40">
              <span className="text-slate-400">Bot Comment Handling:</span>
              <span className="text-rose-400">Counts bot comment as pickup</span>
            </div>
          </div>
        </div>

        {/* Model B: Business-Hours-Aware Extension */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-emerald-500/30 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Proposed: Context-Aware SLA Engine</span>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-mono">Our Extension</span>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-800/40">
              <span className="text-slate-400">Actual SLA Breaches:</span>
              <span className="font-mono font-bold text-emerald-400 text-sm">{business_hours_aware.total_breaches} PRs ({business_hours_aware.breach_rate_pct}%)</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-800/40">
              <span className="text-slate-400">Reported Mean Business Wait:</span>
              <span className="font-mono text-emerald-300 font-bold">{business_hours_aware.mean_waiting_hours.toFixed(1)} business hours</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-800/40">
              <span className="text-slate-400">Reported Median Business Wait:</span>
              <span className="font-mono text-emerald-300 font-bold">{business_hours_aware.median_waiting_hours.toFixed(1)} business hours</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-800/40">
              <span className="text-slate-400">Bot Comment Handling:</span>
              <span className="text-emerald-400 font-semibold">Strictly filtered &amp; unmasked</span>
            </div>
          </div>
        </div>
      </div>

      {/* Concrete Verified Edge Case Examples */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-slate-100 mb-3">Concrete Verified False-Alarm Case Studies</h3>
        <div className="space-y-3">
          {false_positive_examples.map((ex, idx) => (
            <div key={idx} className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-700/60 text-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-semibold text-slate-200">[{ex.repo_name}] {ex.title}</span>
                <span className="text-[11px] font-mono text-emerald-400 font-bold">
                  {ex.business_hours}h biz wait vs. {ex.calendar_hours}h calendar wait
                </span>
              </div>
              <p className="text-slate-400">{ex.explanation}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

