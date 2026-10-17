import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './components/Dashboard';
import { EvaluationView } from './components/EvaluationView';
import { AlertCenter } from './components/AlertCenter';
import { LandingPage } from './components/LandingPage';
import {
  fetchHealth,
  fetchSummary,
  fetchBottlenecks,
  fetchRepositories,
  fetchBacklogTrend,
  fetchComparativeEvaluation,
} from './services/api';
import {
  MetricsSummary,
  BottleneckPR,
  Repository,
  BacklogTrendItem,
  ComparativeEvaluation,
} from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'evaluation' | 'alerts' | 'landing'>('dashboard');
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false);
  const [serviceStatus, setServiceStatus] = useState<string>('CHECKING');
  const [selectedRepo, setSelectedRepo] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [minPriority, setMinPriority] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Analytical Data States
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [bottlenecks, setBottlenecks] = useState<BottleneckPR[]>([]);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [trend, setTrend] = useState<BacklogTrendItem[]>([]);
  const [evaluation, setEvaluation] = useState<ComparativeEvaluation | null>(null);

  const loadAllData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [healthRes, summaryRes, bRes, reposRes, trendRes, evalRes] = await Promise.all([
        fetchHealth(),
        fetchSummary(selectedRepo, isDemoMode),
        fetchBottlenecks(selectedRepo, selectedStatus, minPriority, isDemoMode),
        fetchRepositories(isDemoMode),
        fetchBacklogTrend(30, isDemoMode),
        fetchComparativeEvaluation(isDemoMode),
      ]);

      setServiceStatus(healthRes.status);
      setSummary(summaryRes);
      setBottlenecks(bRes.bottlenecks);
      setRepositories(reposRes);
      setTrend(trendRes);
      setEvaluation(evalRes);
    } catch (err) {
      console.error('Failed to load application data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedRepo, selectedStatus, minPriority, isDemoMode]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-sky-500 selection:text-white">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isDemoMode={isDemoMode}
        setIsDemoMode={setIsDemoMode}
        serviceStatus={serviceStatus}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <Dashboard
            summary={summary}
            bottlenecks={bottlenecks}
            repositories={repositories}
            trend={trend}
            selectedRepo={selectedRepo}
            setSelectedRepo={setSelectedRepo}
            selectedStatus={selectedStatus}
            setSelectedStatus={setSelectedStatus}
            minPriority={minPriority}
            setMinPriority={setMinPriority}
            onRefresh={loadAllData}
            isLoading={isLoading}
          />
        )}

        {activeTab === 'evaluation' && (
          <EvaluationView evaluation={evaluation} />
        )}

        {activeTab === 'alerts' && (
          <AlertCenter />
        )}

        {activeTab === 'landing' && (
          <LandingPage onEnterDashboard={() => setActiveTab('dashboard')} />
        )}
      </main>

      <footer className="border-t border-slate-800 bg-slate-900/50 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <span>Engineering Delivery Bottleneck Analyzer &bull; Built on </span>
            <a
              href="https://github.com/apache/devlake"
              target="_blank"
              rel="noreferrer"
              className="text-sky-400 hover:underline font-medium"
            >
              Apache DevLake v1.0.2
            </a>
            <span> (Apache License 2.0)</span>
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>FastAPI + SQLite + React 18</span>
            <span>&bull;</span>
            <button
              onClick={() => setActiveTab('landing')}
              className="hover:text-slate-200 transition"
            >
              Architecture &amp; Quickstart
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
