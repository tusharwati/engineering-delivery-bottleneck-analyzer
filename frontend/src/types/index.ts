export interface PriorityFactor {
  name: string;
  score: number;
  max_score: number;
  reason: string;
}

export interface RepositoryBaseline {
  repo_id: string;
  sample_count: number;
  min_sample_required: number;
  status: 'SUFFICIENT_SAMPLE' | 'INSUFFICIENT_SAMPLE';
  median_hours: number;
  p90_hours: number;
  fallback_sla_hours: number;
  effective_target_hours: number;
  unit: string;
}

export interface BottleneckPR {
  id: string;
  repo_id: string;
  repo_name: string;
  title: string;
  status: string;
  author_id: string;
  author_name: string;
  created_date: string;
  is_draft: boolean;
  additions: number;
  deletions: number;
  lines_changed: number;
  comment_count: number;
  business_waiting_hours: number;
  calendar_waiting_hours: number;
  non_working_hours: number;
  sla_target_hours: number;
  sla_breached: boolean;
  sla_status: 'BREACHED' | 'AT_RISK' | 'HEALTHY';
  sla_ratio: number;
  priority_score: number;
  priority_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  priority_factors: PriorityFactor[];
  repo_baseline?: RepositoryBaseline | null;
  is_bot_filtered?: boolean;
}

export interface MetricsSummary {
  total_open_prs: number;
  awaiting_review_count: number;
  sla_breached_count: number;
  sla_breach_rate: number;
  median_business_wait_hours: number;
  median_calendar_wait_hours: number;
  non_working_hours_filtered: number;
  configured_sla_hours: number;
  timezone: string;
  working_hours: string;
}

export interface Repository {
  id: string;
  name: string;
  url: string;
  description: string;
  total_prs: number;
  open_prs: number;
  baseline?: RepositoryBaseline | null;
}

export interface BacklogTrendItem {
  date: string;
  opened: number;
  merged: number;
  net_change: number;
  backlog_estimate: number;
}

export interface ComparativeEvaluation {
  dataset_size: number;
  configured_sla_target_hours: number;
  naive_wall_clock: {
    total_breaches: number;
    breach_rate_pct: number;
    mean_waiting_hours: number;
    median_waiting_hours: number;
  };
  business_hours_aware: {
    total_breaches: number;
    breach_rate_pct: number;
    mean_waiting_hours: number;
    median_waiting_hours: number;
  };
  distortion_analysis: {
    false_positive_alerts_eliminated: number;
    false_alert_reduction_pct: number;
    bot_comments_filtered_count: number;
    total_non_working_hours_filtered: number;
  };
  false_positive_examples: Array<{
    id: string;
    title: string;
    repo_name: string;
    calendar_hours: number;
    business_hours: number;
    explanation: string;
  }>;
}

export interface AlertAuditRecord {
  id: number;
  alert_type: string;
  entity_id: string;
  pr_title: string;
  repo_name: string;
  hours_waiting: number;
  message: string;
  status: string;
  dry_run: boolean;
  sent_at: string;
}
