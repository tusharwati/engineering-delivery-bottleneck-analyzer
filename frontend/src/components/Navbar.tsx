import React from 'react';
import { Activity, AlertTriangle, BookOpen, Layers, ShieldCheck, Zap } from 'lucide-react';

interface NavbarProps {
  activeTab: 'dashboard' | 'evaluation' | 'alerts' | 'landing';
  setActiveTab: (tab: 'dashboard' | 'evaluation' | 'alerts' | 'landing') => void;
  isDemoMode: boolean;
  setIsDemoMode: (val: boolean) => void;
  serviceStatus: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isDemoMode,
  setIsDemoMode,
  serviceStatus,
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
      {isDemoMode && (
        <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-1 text-center text-xs font-medium text-amber-300 flex items-center justify-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span>DEMONSTRATION MODE ACTIVE — Displaying isolated synthetic testbed data. No live repository connections required.</span>
        </div>
      )}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Info */}
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setActiveTab('landing')}
              className="flex items-center gap-2.5 text-left focus:outline-none group"
            >
              <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 group-hover:border-sky-500/40 transition">
                <Layers className="w-5 h-5 text-sky-400" />
              </div>
              <div>
                <span className="font-semibold text-slate-100 tracking-tight block">
                  Delivery Bottleneck Analyzer
                </span>
                <span className="text-xs text-slate-400 block">
                  Apache DevLake Companion <span className="text-sky-400 font-mono font-medium">v1.0.2</span>
                </span>
              </div>
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 sm:gap-2">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                activeTab === 'dashboard'
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Queue Analytics</span>
            </button>
            <button
              onClick={() => setActiveTab('evaluation')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                activeTab === 'evaluation'
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>SLA Benchmark</span>
            </button>
            <button
              onClick={() => setActiveTab('alerts')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                activeTab === 'alerts'
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Alert Center</span>
            </button>
            <button
              onClick={() => setActiveTab('landing')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                activeTab === 'landing'
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>Architecture</span>
            </button>
          </nav>

          {/* Right Controls: Status & Demo Mode Toggle */}
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300">
              <span className={`w-2 h-2 rounded-full ${serviceStatus === 'UP' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span>Backend: {serviceStatus}</span>
            </div>

            <button
              onClick={() => setIsDemoMode(!isDemoMode)}
              className={`px-3 py-1 rounded-md text-xs font-semibold border transition flex items-center gap-1.5 ${
                isDemoMode
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30'
                  : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
              }`}
            >
              <span>Demo Mode</span>
              <span className={`w-1.5 h-1.5 rounded-full ${isDemoMode ? 'bg-amber-400' : 'bg-slate-500'}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
