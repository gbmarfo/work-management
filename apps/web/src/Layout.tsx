import { NavLink, Outlet, Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from './AuthContext';
import {
  IconAssets,
  IconCorrective,
  IconCostCenter,
  IconDashboard,
  IconLocation,
  IconLogout,
  IconMeter,
  IconPM,
  IconParts,
  IconPeople,
  IconPurchase,
  IconRequest,
  IconSettings,
  IconWorkOrder,
} from './components/icons';

type NavItem = { to: string; label: string; end?: boolean; icon: ReactNode };
type NavSection = { label: string; items: NavItem[] };

const adminSections: NavSection[] = [
  {
    label: 'Overview',
    items: [{ to: '/', label: 'Dashboard', end: true, icon: <IconDashboard /> }],
  },
  {
    label: 'Operations',
    items: [
      { to: '/work-orders', label: 'Work Orders', icon: <IconWorkOrder /> },
      { to: '/service-requests', label: 'Service Requests', icon: <IconRequest /> },
      { to: '/corrective-maintenance', label: 'Corrective Maintenance', icon: <IconCorrective /> },
      { to: '/pm', label: 'Preventive Maintenance', icon: <IconPM /> },
      { to: '/meter-readings', label: 'Meter Readings', icon: <IconMeter /> },
    ],
  },
  {
    label: 'Assets & Inventory',
    items: [
      { to: '/assets', label: 'Assets', icon: <IconAssets /> },
      { to: '/parts', label: 'Parts', icon: <IconParts /> },
      { to: '/locations', label: 'Locations', icon: <IconLocation /> },
      { to: '/cost-centers', label: 'Cost Centers', icon: <IconCostCenter /> },
    ],
  },
  {
    label: 'Administration',
    items: [
      { to: '/personnel', label: 'Personnel', icon: <IconPeople /> },
      { to: '/purchase-orders', label: 'Purchase Orders', icon: <IconPurchase /> },
      { to: '/configurations', label: 'Configurations', icon: <IconSettings /> },
    ],
  },
];

const technicianSections: NavSection[] = [
  {
    label: 'My Work',
    items: [
      { to: '/work-orders', label: 'Work Orders', end: true, icon: <IconWorkOrder /> },
      { to: '/corrective-maintenance', label: 'Corrective Maintenance', icon: <IconCorrective /> },
      { to: '/assets', label: 'Assets', icon: <IconAssets /> },
      { to: '/pm', label: 'PM Queue', icon: <IconPM /> },
      { to: '/meter-readings', label: 'Meter Readings', icon: <IconMeter /> },
    ],
  },
];

const requesterSections: NavSection[] = [
  {
    label: 'Requests',
    items: [{ to: '/service-requests', label: 'My Requests', end: true, icon: <IconRequest /> }],
  },
];

function initials(email: string) {
  const part = email.split('@')[0] ?? email;
  return part.slice(0, 2).toUpperCase();
}

function pageLabel(pathname: string): string {
  const formLabels: [string, string, string][] = [
    ['/assets', 'New Asset', 'Edit Asset'],
    ['/work-orders', 'New Work Order', 'Edit Work Order'],
    ['/service-requests', 'New Service Request', 'Edit Service Request'],
    ['/parts', 'New Part', 'Edit Part'],
    ['/personnel', 'New Personnel', 'Edit Personnel'],
    ['/locations', 'New Location', 'Edit Location'],
    ['/cost-centers', 'New Cost Center', 'Edit Cost Center'],
    ['/purchase-orders', 'New Purchase Order', 'Edit Purchase Order'],
    ['/corrective-maintenance', 'New CM Job', 'Edit CM Job'],
    ['/pm/tasks', 'New Asset Task', 'Edit Asset Task'],
  ];

  for (const [prefix, newLabel, editLabel] of formLabels) {
    if (pathname.startsWith(prefix)) {
      if (pathname.includes('/new')) return newLabel;
      if (pathname.includes('/edit')) return editLabel;
    }
  }

  if (pathname.startsWith('/assets') && pathname.includes('/attachments')) return 'Asset Attachments';
  if (pathname === '/meter-readings/record') return 'Record Meter Reading';
  if (pathname.startsWith('/meter-readings/groups/new')) return 'New Meter Group';

  const listLabels: [string, string][] = [
    ['/', 'Dashboard'],
    ['/assets', 'Assets'],
    ['/work-orders', 'Work Orders'],
    ['/service-requests', 'Service Requests'],
    ['/parts', 'Parts'],
    ['/pm', 'Preventive Maintenance'],
    ['/corrective-maintenance', 'Corrective Maintenance'],
    ['/personnel', 'Personnel'],
    ['/purchase-orders', 'Purchase Orders'],
    ['/locations', 'Locations'],
    ['/cost-centers', 'Cost Centers'],
    ['/meter-readings', 'Meter Readings'],
    ['/configurations', 'Configurations'],
  ];

  for (const [prefix, label] of listLabels) {
    if (prefix === '/' ? pathname === '/' : pathname.startsWith(prefix)) return label;
  }

  return 'Enterprise EAM';
}

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const sections =
    user?.role === 'REQUESTER'
      ? requesterSections
      : user?.role === 'TECHNICIAN'
        ? technicianSections
        : adminSections;

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">
            <div className="sidebar-logo">EAM</div>
            <div>
              <h1>Enterprise EAM</h1>
              <div className="subtitle">Facilities & Asset Management</div>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {sections.map((section) => (
            <div key={section.label} className="nav-section">
              <div className="nav-section-label">{section.label}</div>
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
                >
                  {item.icon}
                  {item.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-card">
            <div className="user-avatar">{initials(user?.email ?? 'U')}</div>
            <div className="user-details">
              <div className="email">{user?.email}</div>
              <div className="role">{user?.role}</div>
            </div>
          </div>
          <button type="button" className="btn btn-logout btn-sm" onClick={logout}>
            <IconLogout size={16} />
            Sign out
          </button>
        </div>
      </aside>

      <div className="main">
        <div className="main-topbar">
          <span className="main-topbar-title">{pageLabel(location.pathname)}</span>
        </div>
        <div className="main-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="login-panel" style={{ minHeight: '100vh', width: '100%' }}>
        <LoadingScreen />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function LoadingScreen() {
  return (
    <div className="loading-state">
      <div className="loading-spinner" />
      <span>Loading application…</span>
    </div>
  );
}
