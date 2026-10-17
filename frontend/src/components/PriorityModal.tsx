import React from 'react';
import { X, ShieldAlert, CheckCircle, HelpCircle, Layers } from 'lucide-react';
import { BottleneckPR } from '../types';

interface PriorityModalProps {
  pr: BottleneckPR | null;
  onClose: () => void;
}

export const PriorityModal: React.FC<PriorityModalProps> = ({ pr, onClose }) => {
  if (!pr) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Bottleneck Priority Explanation</h3>
            <p className="text-xs text-slate-400 font-mono">{pr.repo_name}</p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/60 mb-5">
          <div className="text-sm font-semibold text-slate-100 mb-1">{pr.title}</div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
            <span>Author: <strong className="text-slate-200">{pr.author_name}</strong></span>
            <span>•</span>
            <span>Business Wait: <strong className="text-emerald-400">{pr.business_waiting_hours.toFixed(1)}h</strong></span>
            <span>•</span>
            <span>Calendar Wait: <strong className="text-slate-300">{pr.calendar_waiting_hours.toFixed(1)}h</strong></span>
          </div>
        </div>

        <div className="flex items-center justify-between p-3 rounded-lg bg-sky-950/30 border border-sky-800/50 mb-5">
          <div className="text-xs text-sky-300">
            <span className="font-semibold block">Total Urgency Score:</span>
            <span className="text-[11px] text-sky-400/80">Computed via rule-based explainable multi-factor formula</span>
          </div>
          <div className="text-right">
            <span className="text-2xl font-black text-white">{pr.priority_score}</span>
            <span className="text-xs font-semibold ml-1 text-sky-400">/ 100</span>
            <span className="block text-[10px] uppercase font-bold tracking-wider text-rose-400">{pr.priority_level}</span>
          </div>
        </div>

        <div className="space-y-3 mb-6 max-h-72 overflow-y-auto pr-1">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Contributing Factors Breakdown</h4>
          {pr.priority_factors.map((factor, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-slate-800/30 border border-slate-800">
              <div className="flex items-center justify-between mb-1.5 text-xs">
                <span className="font-semibold text-slate-200">{factor.name}</span>
                <span className="font-mono font-bold text-sky-400">
                  +{factor.score} <span className="text-slate-500 font-normal">/ {factor.max_score} pts</span>
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 mb-2 overflow-hidden">
                <div
                  className="bg-sky-500 h-1.5 rounded-full"
                  style={{ width: `${(factor.score / factor.max_score) * 100}%` }}
                />
              </div>
              <p className="text-xs text-slate-400">{factor.reason}</p>
            </div>
          ))}
        </div>

        <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
          <div className="flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            <span>Strictly measures PR urgency. Does not rank individual developers.</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
