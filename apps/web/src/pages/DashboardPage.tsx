import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import LoadingState from '../components/LoadingState';
import { api, type ExecutiveDashboard, type WorkOrderTrendPoint } from '../api';

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
const pct = (n: number) => `${n.toFixed(1)}%`;

function healthTone(score: number) {
  if (score >= 85) return 'excellent';
  if (score >= 70) return 'good';
  if (score >= 50) return 'fair';
  return 'critical';
}

function HealthRing({ score }: { score: number }) {
  const tone = healthTone(score);
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className={`exec-health-ring exec-health-ring--${tone}`}>
      <svg viewBox="0 0 128 128" aria-hidden>
        <circle className="exec-health-ring-track" cx="64" cy="64" r={radius} />
        <circle
          className="exec-health-ring-progress"
          cx="64"
          cy="64"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="exec-health-ring-label">
        <span className="exec-health-ring-value">{score}</span>
        <span className="exec-health-ring-caption">Health Index</span>
      </div>
    </div>
  );
}

function TrendChart({ points }: { points: WorkOrderTrendPoint[] }) {
  const max = Math.max(1, ...points.flatMap((p) => [p.completed, p.opened]));

  return (
    <div className="exec-trend-chart">
      <div className="exec-trend-bars">
        {points.map((p) => (
          <div key={p.month} className="exec-trend-group">
            <div className="exec-trend-bar-pair">
              <div
                className="exec-trend-bar exec-trend-bar--opened"
                style={{ height: `${(p.opened / max) * 100}%` }}
                title={`Opened: ${p.opened}`}
              />
              <div
                className="exec-trend-bar exec-trend-bar--completed"
                style={{ height: `${(p.completed / max) * 100}%` }}
                title={`Completed: ${p.completed}`}
              />
            </div>
            <span className="exec-trend-month">{p.month.split(' ')[0]}</span>
          </div>
        ))}
      </div>
      <div className="exec-chart-legend">
        <span><i className="exec-legend-dot exec-legend-dot--opened" /> Opened</span>
        <span><i className="exec-legend-dot exec-legend-dot--completed" /> Completed</span>
      </div>
    </div>
  );
}

function MixDonut({ mix }: { mix: ExecutiveDashboard['work_order_mix'] }) {
  const total = mix.corrective + mix.preventive + mix.general || 1;
  const cPct = (mix.corrective / total) * 100;
  const pPct = (mix.preventive / total) * 100;
  const gradient = `conic-gradient(
    #dc2626 0 ${cPct}%,
    #2563eb ${cPct}% ${cPct + pPct}%,
    #64748b ${cPct + pPct}% 100%
  )`;

  return (
    <div className="exec-mix">
      <div className="exec-mix-donut" style={{ background: gradient }}>
        <div className="exec-mix-donut-hole">
          <strong>{total}</strong>
          <span>Open</span>
        </div>
      </div>
      <ul className="exec-mix-legend">
        <li><span className="exec-mix-swatch exec-mix-swatch--cm" /> Corrective <strong>{mix.corrective}</strong></li>
        <li><span className="exec-mix-swatch exec-mix-swatch--pm" /> Preventive <strong>{mix.preventive}</strong></li>
        <li><span className="exec-mix-swatch exec-mix-swatch--gen" /> General <strong>{mix.general}</strong></li>
      </ul>
    </div>
  );
}

function PriorityBars({ breakdown }: { breakdown: ExecutiveDashboard['priority_breakdown'] }) {
  const items = [
    { key: 'critical', label: 'Critical', value: breakdown.critical, tone: 'danger' },
    { key: 'high', label: 'High', value: breakdown.high, tone: 'warning' },
    { key: 'medium', label: 'Medium', value: breakdown.medium, tone: 'info' },
    { key: 'low', label: 'Low', value: breakdown.low, tone: 'success' },
  ];
  const max = Math.max(1, ...items.map((i) => i.value));

  return (
    <div className="exec-priority-bars">
      {items.map((item) => (
        <div key={item.key} className="exec-priority-row">
          <span className="exec-priority-label">{item.label}</span>
          <div className="exec-priority-track">
            <div
              className={`exec-priority-fill exec-priority-fill--${item.tone}`}
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
          <span className="exec-priority-count">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

function statusClass(status: string) {
  if (status === 'OVERDUE') return 'badge-danger';
  if (status === 'IN_PROGRESS') return 'badge-progress';
  if (status === 'COMPLETED') return 'badge-completed';
  if (status === 'DOWN' || status === 'OUT_OF_SERVICE') return 'badge-danger';
  return 'badge-open';
}

function kindLabel(kind: string) {
  if (kind === 'work_order') return 'Work Order';
  if (kind === 'service_request') return 'Request';
  return 'Asset';
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['executive-dashboard'],
    queryFn: () => api<ExecutiveDashboard>('/v1/reports/executive'),
  });

  if (isLoading || !data) return <LoadingState label="Loading executive dashboard…" />;

  const generated = new Date(data.generated_at).toLocaleString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });

  const kpis = [
    {
      label: 'Asset Availability',
      value: pct(data.asset_availability_pct),
      sub: `${data.active_assets} of ${data.total_assets} assets operational`,
      tone: data.asset_availability_pct >= 95 ? 'success' : 'warning',
    },
    {
      label: 'WO Completion (30d)',
      value: pct(data.wo_completion_rate_pct),
      sub: `${data.completed_last_30_days} jobs closed this month`,
      tone: data.wo_completion_rate_pct >= 80 ? 'success' : 'info',
    },
    {
      label: 'PM Compliance',
      value: pct(data.pm_compliance_pct),
      sub: `${data.pending_pm_queue} tasks in queue`,
      tone: data.pm_compliance_pct >= 90 ? 'success' : 'warning',
    },
    {
      label: 'Portfolio Value',
      value: currency.format(data.total_asset_value),
      sub: `${data.critical_assets} critical assets monitored`,
      tone: 'info',
    },
  ];

  const alerts = [
    { label: 'Overdue Jobs', value: data.overdue_work_orders, path: '/work-orders', tone: 'danger' as const },
    { label: 'Open CM', value: data.open_corrective_maintenance, path: '/corrective-maintenance', tone: 'danger' as const },
    { label: 'Open Requests', value: data.open_service_requests, path: '/service-requests', tone: 'warning' as const },
    { label: 'Low Stock', value: data.parts_below_reorder, path: '/parts', tone: 'warning' as const },
    { label: 'Assets Down', value: data.down_assets, path: '/assets', tone: 'danger' as const },
    { label: 'Open WOs', value: data.open_work_orders, path: '/work-orders', tone: 'info' as const },
  ];

  return (
    <div className="exec-dashboard">
      <section className="exec-hero">
        <div className="exec-hero-copy">
          <p className="exec-hero-eyebrow">Executive Operations Brief · {data.site_name}</p>
          <h1 className="exec-hero-title">Maintenance &amp; Reliability Overview</h1>
          <p className="exec-hero-lead">
            Real-time visibility across assets, work execution, and preventive programs.
            {data.avg_resolution_days != null && (
              <> Average resolution time is <strong>{data.avg_resolution_days} days</strong>.</>
            )}
          </p>
          <p className="exec-hero-meta">Updated {generated}</p>
          <div className="exec-hero-actions">
            <Link to="/work-orders" className="btn btn-primary">View Work Orders</Link>
            <Link to="/assets" className="btn btn-secondary">Asset Register</Link>
          </div>
        </div>
        <div className="exec-hero-score">
          <HealthRing score={data.health_score} />
          <p className={`exec-health-verdict exec-health-verdict--${healthTone(data.health_score)}`}>
            {data.health_score >= 85 && 'Operations performing within target'}
            {data.health_score >= 70 && data.health_score < 85 && 'Minor attention areas identified'}
            {data.health_score >= 50 && data.health_score < 70 && 'Several items require leadership review'}
            {data.health_score < 50 && 'Immediate intervention recommended'}
          </p>
        </div>
      </section>

      <section className="exec-kpi-row">
        {kpis.map((kpi) => (
          <article key={kpi.label} className={`exec-kpi exec-kpi--${kpi.tone}`}>
            <span className="exec-kpi-label">{kpi.label}</span>
            <span className="exec-kpi-value">{kpi.value}</span>
            <span className="exec-kpi-sub">{kpi.sub}</span>
          </article>
        ))}
      </section>

      <section className="exec-alert-strip">
        {alerts.map((a) => (
          <Link key={a.label} to={a.path} className={`exec-alert exec-alert--${a.tone}`}>
            <span className="exec-alert-value">{a.value}</span>
            <span className="exec-alert-label">{a.label}</span>
          </Link>
        ))}
      </section>

      <div className="exec-grid">
        <section className="exec-panel exec-panel--wide">
          <header className="exec-panel-header">
            <div>
              <h2>Work Order Throughput</h2>
              <p>Six-month trend of jobs opened vs. completed</p>
            </div>
          </header>
          <TrendChart points={data.work_order_trend} />
        </section>

        <section className="exec-panel">
          <header className="exec-panel-header">
            <div>
              <h2>Open Work Mix</h2>
              <p>Distribution by maintenance type</p>
            </div>
          </header>
          <MixDonut mix={data.work_order_mix} />
        </section>

        <section className="exec-panel">
          <header className="exec-panel-header">
            <div>
              <h2>Priority Exposure</h2>
              <p>Open work by urgency level</p>
            </div>
          </header>
          <PriorityBars breakdown={data.priority_breakdown} />
        </section>

        <section className="exec-panel exec-panel--wide">
          <header className="exec-panel-header">
            <div>
              <h2>Items Requiring Attention</h2>
              <p>Overdue jobs, open requests, and offline assets</p>
            </div>
            <Link to="/corrective-maintenance" className="exec-panel-link">View all CM →</Link>
          </header>
          {data.attention_items.length === 0 ? (
            <div className="exec-empty-attention">No critical items — operations are on track.</div>
          ) : (
            <div className="exec-attention-table-wrap">
              <table className="exec-attention-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Type</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Due</th>
                  </tr>
                </thead>
                <tbody>
                  {data.attention_items.map((item) => (
                    <tr key={`${item.kind}-${item.id}`}>
                      <td>
                        <Link to={item.path} className="exec-attention-title">{item.title}</Link>
                        <span className="exec-attention-sub">{item.subtitle}</span>
                      </td>
                      <td>{kindLabel(item.kind)}</td>
                      <td>{item.priority ?? '—'}</td>
                      <td><span className={`badge ${statusClass(item.status)}`}>{item.status.replace(/_/g, ' ')}</span></td>
                      <td>{item.due_date ? new Date(item.due_date).toLocaleDateString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
