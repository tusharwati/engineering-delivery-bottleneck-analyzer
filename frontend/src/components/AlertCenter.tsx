import React, { useState, useEffect } from 'react';
import { Bell, ShieldCheck, Play, CheckCircle2, History, AlertTriangle } from 'lucide-react';
import { AlertAuditRecord } from '../types';
import { fetchAlertHistory, triggerAlertCheck } from '../services/api';

export const AlertCenter: React.FC = () => {
  const [history, setHistory] = useState<AlertAuditRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);

  const loadHistory = async () => {
    const records = await fetchAlertHistory();
    setHistory(records);
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleTrigger = async (dryRun: boolean) => {
    setIsLoading(true);
    try {
      const res = await triggerAlertCheck(dryRun, 40);
      setLastResult(res);
      await loadHistory();
    } catch (err: any) {
      alert(`Alert execution error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Alert Engine Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Bell className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Automated Review SLA Alert Engine</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluates active review SLA breaches with deduplication state and dry-run safety
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => handleTrigger(true)}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow transition disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{isLoading ? 'Scanning Queue...' : 'Run Test Scan (Dry-Run)'}</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-slate-800 text-xs">
          <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/60">
            <span className="text-slate-400 block mb-1 font-medium">Delivery Mode</span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>Dry-Run Active (No Spam)</span>
            </span>
            <p className="text-[11px] text-slate-500 mt-1">Logs payload to SQLite audit store without outbound calls</p>
          </div>

          <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/60">
            <span className="text-slate-400 block mb-1 font-medium">Deduplication Guard</span>
            <span className="text-sky-300 font-semibold font-mono">24 Hours Cooldown</span>
            <p className="text-[11px] text-slate-500 mt-1">Suppresses repeated notifications for the same breach</p>
          </div>

          <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/60">
            <span className="text-slate-400 block mb-1 font-medium">Secret Protection</span>
            <span className="text-purple-300 font-semibold">Automatic Token Redaction</span>
            <p className="text-[11px] text-slate-500 mt-1">Slack webhooks and GitHub tokens masked in all records</p>
          </div>
        </div>

        {lastResult && (
          <div className="mt-5 p-4 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-mono">
            <div className="flex items-center justify-between text-slate-300 mb-2">
              <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>Scan Completed: {lastResult.alerts_dispatched} alert(s) evaluated</span>
              </span>
              <span className="text-slate-500">{lastResult.timestamp}</span>
            </div>
            <p className="text-slate-400 mb-2">
              Suppressed by deduplication: <strong>{lastResult.alerts_suppressed_by_dedup}</strong> | Mode: <strong>{lastResult.dry_run ? 'DRY_RUN' : 'LIVE'}</strong>
            </p>
            {lastResult.dispatched_details?.length > 0 && (
              <div className="space-y-1.5 mt-2 pt-2 border-t border-slate-700">
                {lastResult.dispatched_details.map((d: any, idx: number) => (
                  <div key={idx} className="text-[11px] text-slate-300 flex items-center justify-between">
                    <span className="truncate max-w-md">• [{d.repo_name}] {d.title}</span>
                    <span className="text-rose-400 font-semibold">{d.business_waiting_hours}h wait ({d.priority_score} pts)</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Audit History Log */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-sky-400" />
            <h3 className="text-sm font-semibold text-slate-100">Notification Audit History (SQLite)</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">{history.length} records</span>
        </div>

        {history.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No alerts dispatched yet. Click &quot;Run Test Scan&quot; above to simulate an SLA alert.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/60 text-slate-400 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Event Type</th>
                  <th className="py-3 px-4">Target PR / Entity</th>
                  <th className="py-3 px-4">Repository</th>
                  <th className="py-3 px-4">Wait Time</th>
                  <th className="py-3 px-4">Delivery Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {history.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-800/30 transition font-mono text-[11px]">
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                      {new Date(rec.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-sky-400 font-semibold">
                      {rec.alert_type}
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-slate-200" title={rec.pr_title || rec.entity_id}>
                      {rec.pr_title || rec.entity_id}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                      {rec.repo_name || '—'}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-emerald-400">
                      {rec.hours_waiting ? `${rec.hours_waiting.toFixed(1)}h` : '—'}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                        {rec.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
