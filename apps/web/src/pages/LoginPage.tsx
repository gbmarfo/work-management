import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();

  if (user) return <Navigate to="/" replace />;

  const [email, setEmail] = useState('admin@eam.demo');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="login-brand-inner">
          <div className="login-brand-logo">EAM</div>
          <h1>Enterprise Asset Management</h1>
          <p>
            Manage assets, work orders, preventive maintenance, and inventory from one
            professional workspace built for facilities teams.
          </p>
          <ul className="login-brand-features">
            <li>Unified work order & service request tracking</li>
            <li>Preventive maintenance scheduling</li>
            <li>Parts inventory & procurement</li>
            <li>Personnel & location management</li>
          </ul>
        </div>
      </div>

      <div className="login-panel">
        <div className="login-card">
          <h2>Sign in</h2>
          <p className="login-subtitle">Enter your credentials to access the system</p>
          {error && <div className="error">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                autoComplete="username"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.25rem' }} disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
          <div className="login-demo">
            <strong>Demo account:</strong> admin@eam.demo / admin123
          </div>
        </div>
      </div>
    </div>
  );
}
