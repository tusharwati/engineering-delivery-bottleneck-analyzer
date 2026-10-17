import { BottleneckPR, MetricsSummary, Repository, BacklogTrendItem, ComparativeEvaluation, AlertAuditRecord } from '../types';
import { DEMO_SUMMARY, DEMO_BOTTLENECK_PRS, DEMO_REPOSITORIES, DEMO_BACKLOG_TREND, DEMO_EVALUATION } from '../mock/demoData';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<{ status: string; pinned_devlake_version: string; database_connected: boolean }> {
  try {
    const res = await fetch(`${BASE_URL}/api/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return { status: 'OFFLINE', pinned_devlake_version: 'v1.0.2', database_connected: false };
  }
}

export async function fetchSummary(repoId: string = 'all', isDemo: boolean = false): Promise<MetricsSummary> {
  if (isDemo) return DEMO_SUMMARY;
  try {
    const url = repoId && repoId !== 'all' 
      ? `${BASE_URL}/api/metrics/summary?repo_id=${encodeURIComponent(repoId)}` 
      : `${BASE_URL}/api/metrics/summary`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend unavailable, using synthetic demo summary:", err);
    return DEMO_SUMMARY;
  }
}

export async function fetchBottlenecks(
  repoId: string = 'all',
  slaStatus: string = '',
  minPriority: number = 0,
  isDemo: boolean = false
): Promise<{ count: number; bottlenecks: BottleneckPR[] }> {
  if (isDemo) {
    let prs = DEMO_BOTTLENECK_PRS;
    if (repoId && repoId !== 'all') prs = prs.filter(p => p.repo_id === repoId);
    if (slaStatus) prs = prs.filter(p => p.sla_status === slaStatus);
    if (minPriority > 0) prs = prs.filter(p => p.priority_score >= minPriority);
    return { count: prs.length, bottlenecks: prs };
  }

  try {
    const params = new URLSearchParams();
    if (repoId && repoId !== 'all') params.set('repo_id', repoId);
    if (slaStatus) params.set('sla_status', slaStatus);
    if (minPriority > 0) params.set('min_priority', minPriority.toString());

    const res = await fetch(`${BASE_URL}/api/bottlenecks?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend unavailable, using synthetic demo bottlenecks:", err);
    return { count: DEMO_BOTTLENECK_PRS.length, bottlenecks: DEMO_BOTTLENECK_PRS };
  }
}

export async function fetchRepositories(isDemo: boolean = false): Promise<Repository[]> {
  if (isDemo) return DEMO_REPOSITORIES;
  try {
    const res = await fetch(`${BASE_URL}/api/repositories`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.repositories || [];
  } catch (err) {
    console.warn("Backend unavailable, using synthetic demo repositories:", err);
    return DEMO_REPOSITORIES;
  }
}

export async function fetchBacklogTrend(days: number = 30, isDemo: boolean = false): Promise<BacklogTrendItem[]> {
  if (isDemo) return DEMO_BACKLOG_TREND;
  try {
    const res = await fetch(`${BASE_URL}/api/backlog/trend?days=${days}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.trend || [];
  } catch (err) {
    console.warn("Backend unavailable, using synthetic demo trend:", err);
    return DEMO_BACKLOG_TREND;
  }
}

export async function fetchComparativeEvaluation(isDemo: boolean = false): Promise<ComparativeEvaluation> {
  if (isDemo) return DEMO_EVALUATION;
  try {
    const res = await fetch(`${BASE_URL}/api/evaluation/compare`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend unavailable, using synthetic demo evaluation:", err);
    return DEMO_EVALUATION;
  }
}

export async function fetchAlertHistory(): Promise<AlertAuditRecord[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/alerts/history`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.history || [];
  } catch {
    return [];
  }
}

export async function triggerAlertCheck(dryRun: boolean = true, minPriority: number = 50): Promise<any> {
  const res = await fetch(`${BASE_URL}/api/alerts/trigger-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dry_run: dryRun, min_priority_score: minPriority }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}
