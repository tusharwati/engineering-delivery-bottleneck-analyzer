import React, { useState } from 'react';
import {
  GitPullRequest,
  Clock,
  AlertTriangle,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { BottleneckPR, MetricsSummary, Repository, BacklogTrendItem } from '../types';
import { StatCard } from './StatCard';
import { FilterBar } from './FilterBar';
import { WallClockVsBusinessChart } from './WallClockVsBusinessChart';
import { BacklogChart } from './BacklogChart';
import { RepositoriesComparison } from './RepositoriesComparison';
import { WaitingPrTable } from './WaitingPrTable';
import { PriorityModal } from './PriorityModal';

interface DashboardProps {
  summary: MetricsSummary | null;
  bottlenecks: BottleneckPR[];
  repositories: Repository[];
  trend: BacklogTrendItem[];
  selectedRepo: string;
  setSelectedRepo: (id: string) => void;
  selectedStatus: string;
  setSelectedStatus: (status: string) => void;
  minPriority: number;
  setMinPriority: (p: number) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const Dashboard: React.FC<DashboardProps> = ({
  summary,
  bottlenecks,
  repositories,
  trend,
  selectedRepo,
  setSelectedRepo,
  selectedStatus,
  setSelectedStatus,
  minPriority,
  setMinPriority,
  onRefresh,
  isLoading,
}) => {
  const [selectedPr, setSelectedPr] = useState<BottleneckPR | null>(null);

  return (
    <div className="space-y-6">
      {/* KPI Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Open Pull Requests"
          value={summary?.total_open_prs ?? '—'}
          subtext="Total active PRs across monitored repositories"
          icon={GitPullRequest}
          variant="default"
        />
        <StatCard
          label="Awaiting Qualifying Review"
          value={summary?.awaiting_review_count ?? '—'}
          subtext="Open PRs with no genuine human review yet"
          icon={Clock}
          variant="warning"
        />
        <StatCard
          label="Review SLA Breached"
          value={summary?.sla_breached_count ?? '—'}
          subtext={`${summary?.sla_breach_rate ?? 0}% breach rate (> ${summary?.configured_sla_hours ?? 8}h business wait)`}
          icon={ShieldAlert}
          variant={(summary?.sla_breached_count ?? 0) > 0 ? 'danger' : 'success'}
        />
        <StatCard
          label="Median Business Wait"
          value={summary ? `${summary.median_business_wait_hours}h` : '—'}
          subtext={`vs. ${summary?.median_calendar_wait_hours ?? 0}h calendar wait (${summary?.non_working_hours_filtered ?? 0}h off-hours filtered)`}
          icon={Sparkles}
          variant="success"
        />
      </div>

      {/* Filter Bar */}
      <FilterBar
        repositories={repositories}
        selectedRepo={selectedRepo}
        setSelectedRepo={setSelectedRepo}
        selectedStatus={selectedStatus}
        setSelectedStatus={setSelectedStatus}
        minPriority={minPriority}
        setMinPriority={setMinPriority}
        onRefresh={onRefresh}
        isLoading={isLoading}
      />

      {/* Comparative Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WallClockVsBusinessChart
          bottlenecks={bottlenecks}
          slaHours={summary?.configured_sla_hours ?? 8.0}
        />
        <BacklogChart trend={trend} />
      </div>

      {/* Repositories Baseline Comparison */}
      <RepositoriesComparison repositories={repositories} />

      {/* Prioritized Waiting PRs Queue Table */}
      <WaitingPrTable
        bottlenecks={bottlenecks}
        onSelectPr={(pr) => setSelectedPr(pr)}
      />

      {/* Priority Scoring Explanation Modal */}
      <PriorityModal
        pr={selectedPr}
        onClose={() => setSelectedPr(null)}
      />
    </div>
  );
};
