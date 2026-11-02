import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './AuthContext';
import Layout, { RequireAuth } from './Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import AssetsPage from './pages/AssetsPage';
import WorkOrdersPage from './pages/WorkOrdersPage';
import ServiceRequestsPage from './pages/ServiceRequestsPage';
import PartsPage from './pages/PartsPage';
import PMPage from './pages/PMPage';
import PersonnelPage from './pages/PersonnelPage';
import PurchaseOrdersPage from './pages/PurchaseOrdersPage';
import LocationsPage from './pages/LocationsPage';
import CostCentersPage from './pages/CostCentersPage';
import MeterReadingsPage from './pages/MeterReadingsPage';
import CorrectiveMaintenancePage from './pages/CorrectiveMaintenancePage';
import ConfigurationsPage from './pages/ConfigurationsPage';

const qc = new QueryClient();

function HomeRedirect() {
  const { user } = useAuth();
  if (user?.role === 'REQUESTER') return <Navigate to="/service-requests" replace />;
  if (user?.role === 'TECHNICIAN') return <Navigate to="/work-orders" replace />;
  return <DashboardPage />;
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route path="/" element={<HomeRedirect />} />
              <Route path="/assets/*" element={<AssetsPage />} />
              <Route path="/work-orders/*" element={<WorkOrdersPage />} />
              <Route path="/service-requests/*" element={<ServiceRequestsPage />} />
              <Route path="/parts/*" element={<PartsPage />} />
              <Route path="/pm/*" element={<PMPage />} />
              <Route path="/corrective-maintenance/*" element={<CorrectiveMaintenancePage />} />
              <Route path="/personnel/*" element={<PersonnelPage />} />
              <Route path="/purchase-orders/*" element={<PurchaseOrdersPage />} />
              <Route path="/locations/*" element={<LocationsPage />} />
              <Route path="/cost-centers/*" element={<CostCentersPage />} />
              <Route path="/meter-readings/*" element={<MeterReadingsPage />} />
              <Route path="/configurations" element={<ConfigurationsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
