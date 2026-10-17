import React from 'react';
import {
  Layers,
  Clock,
  ShieldCheck,
  Zap,
  CheckCircle2,
  Terminal,
  Code2,
  GitPullRequest,
  BarChart3,
  BellRing,
  ArrowRight,
} from 'lucide-react';

interface LandingPageProps {
  onEnterDashboard: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterDashboard }) => {
  return (
    <div className="space-y-16 py-6 animate-fade-in">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto space-y-5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-semibold">
          <Layers className="w-3.5 h-3.5" />
          <span>Apache DevLake v1.0.2 Open-Source Extension</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
          Context-Aware Engineering Delivery Bottleneck Analyzer
        </h1>

        <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
          Standard code-review metrics falsely flag PRs opened over weekends as massive delays while bots mask true human bottlenecks.
          We extend <strong>Apache DevLake</strong> with business-hours SLAs, bot-filtering review detection, learned repository baselines, and explainable prioritization.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <button
            onClick={onEnterDashboard}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold shadow-lg shadow-sky-600/20 transition transform hover:-translate-y-0.5"
          >
            <span>Launch Queue Analytics Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <a
            href="https://github.com/apache/devlake"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold border border-slate-700 transition"
          >
            <span>Upstream Apache DevLake (v1.0.2)</span>
          </a>
        </div>
      </div>

      {/* 1-Minute Pitch: The Problem & The Solution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-900/40 space-y-4">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-sm uppercase tracking-wider">
            <Clock className="w-4 h-4" />
            <span>The Conventional Review Metrics Trap</span>
          </div>
          <h3 className="text-lg font-bold text-white">Why Wall-Clock PR Metrics Fail Engineering Teams</h3>
          <ul className="space-y-3 text-xs sm:text-sm text-slate-300">
            <li className="flex items-start gap-2">
              <span className="text-rose-400 font-bold">1.</span>
              <span><strong>Weekend False Alarms:</strong> A PR submitted Friday at 18:00 and reviewed Monday at 10:00 is reported as a ~64-hour failure by naive metrics, even though only 1.0 business hour elapsed.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-rose-400 font-bold">2.</span>
              <span><strong>Bot Masking:</strong> Automated tools like <code className="text-rose-300">codecov[bot]</code> post comments within 45 seconds of creation, falsely recording immediate review pickup and hiding multi-day human delays.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-rose-400 font-bold">3.</span>
              <span><strong>Queue Invisibility:</strong> Standard dashboards analyze retrospective closed PRs, leaving stalled in-flight pull requests invisible until it is too late.</span>
            </li>
          </ul>
        </div>

        <div className="p-6 rounded-2xl bg-emerald-950/20 border border-emerald-900/40 space-y-4">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm uppercase tracking-wider">
            <Zap className="w-4 h-4" />
            <span>Our Technical Contribution</span>
          </div>
          <h3 className="text-lg font-bold text-white">How Our Analyzer Transforms Delivery Visibility</h3>
          <ul className="space-y-3 text-xs sm:text-sm text-slate-300">
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 font-bold">1.</span>
              <span><strong>Business-Hours Engine:</strong> Computes exact business time across IANA timezones (default: <code className="text-emerald-300">Asia/Kolkata</code>), working schedules, and holiday calendars with DST safety.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 font-bold">2.</span>
              <span><strong>Verified Review Detection:</strong> Strictly excludes author self-comments and bot accounts; isolates formal reviews (<code className="text-emerald-300">DIFF</code>, <code className="text-emerald-300">REVIEW</code>, <code className="text-emerald-300">APPROVED</code>).</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 font-bold">3.</span>
              <span><strong>Explainable Triage Scoring:</strong> Multi-factor 0-100 score prioritizing active PRs by SLA severity, diff size, and queue congestion without ranking developers.</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Architecture & Tech Stack Highlights */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
        <div>
          <h3 className="text-base font-bold text-white">System Architecture & Clean Separation</h3>
          <p className="text-xs text-slate-400 mt-1">
            Built as a non-invasive analytical companion connecting to Apache DevLake via parameterized read-only queries.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
            <div className="text-sky-400 font-semibold flex items-center gap-1.5">
              <Code2 className="w-4 h-4" />
              <span>FastAPI Backend</span>
            </div>
            <p className="text-slate-400">
              High-throughput Python 3.11 service computing minute-accurate business hours and rule-based priority breakdowns.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
            <div className="text-emerald-400 font-semibold flex items-center gap-1.5">
              <Layers className="w-4 h-4" />
              <span>Apache DevLake v1.0.2</span>
            </div>
            <p className="text-slate-400">
              Handles GitHub API authentication, incremental sync, rate limiting, and domain data normalization.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
            <div className="text-purple-400 font-semibold flex items-center gap-1.5">
              <BarChart3 className="w-4 h-4" />
              <span>React 18 + Vite UI</span>
            </div>
            <p className="text-slate-400">
              Clean dashboard with Recharts visual summaries, modal explanations, and demo testbed toggle.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
            <div className="text-amber-400 font-semibold flex items-center gap-1.5">
              <BellRing className="w-4 h-4" />
              <span>Deduplicated Alerting</span>
            </div>
            <p className="text-slate-400">
              Separate SQLite database managing 24h deduplication cooldowns, dry-run safety, and secret masking.
            </p>
          </div>
        </div>
      </div>

      {/* Quickstart Instructions */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-4">
        <div className="flex items-center gap-2 text-sky-400 font-semibold text-sm">
          <Terminal className="w-4 h-4" />
          <span>Local Quickstart (Native Windows 11 / Linux / macOS)</span>
        </div>
        <p className="text-xs text-slate-300">
          Run locally in under 60 seconds without Docker or cloud accounts using the bundled synthetic seed generator:
        </p>

        <div className="bg-slate-950 rounded-xl p-4 font-mono text-xs text-slate-300 space-y-2 overflow-x-auto border border-slate-800">
          <div className="text-slate-500"># 1. Start Python backend (runs on http://localhost:8000)</div>
          <div>cd backend</div>
          <div>python -m pip install -r requirements.txt</div>
          <div>python -m uvicorn app.main:app --host 0.0.0.0 --port 8000</div>
          <div className="text-slate-500 pt-2"># 2. Start React frontend in another window (runs on http://localhost:5173)</div>
          <div>cd frontend</div>
          <div>npm.cmd install &amp;&amp; npm.cmd run dev</div>
        </div>
      </div>
    </div>
  );
};

