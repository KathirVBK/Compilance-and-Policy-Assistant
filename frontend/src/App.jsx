import React, { useState, useEffect } from 'react';
import Home       from './pages/Home';
import LoginPage  from './pages/LoginPage';
import AdminPanel from './pages/AdminPanel';
import { api }   from './services/api';
import { ThemeToggle } from './components/UI/ThemeToggle';

function App() {
  const [currentUser, setCurrentUser] = useState(() => api.getCurrentUser());
  // Hash-based routing: '' or '#/' → chat, '#/admin' → admin panel
  const [hash, setHash] = useState(window.location.hash || '#/');

  useEffect(() => {
    const onHash = () => setHash(window.location.hash || '#/');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    window.location.hash = '#/';
  };

  const handleLogout = async () => {
    await api.logout();
    setCurrentUser(null);
    window.location.hash = '#/';
  };

  const handleGoAdmin = () => { window.location.hash = '#/admin'; };
  const handleGoHome  = () => { window.location.hash = '#/'; };

  // ── Not logged in → show login ────────────────────────────────────────────
  if (!currentUser) {
    return (
      <div className="App">
        <LoginPage onLoginSuccess={handleLoginSuccess} />
        <ThemeToggle />
      </div>
    );
  }

  // ── Admin panel route ─────────────────────────────────────────────────────
  if (hash === '#/admin' && currentUser.role === 'admin') {
    return (
      <div className="App">
        <AdminPanel currentUser={currentUser} onBack={handleGoHome} />
        <ThemeToggle />
      </div>
    );
  }

  // ── Main chat ─────────────────────────────────────────────────────────────
  return (
    <div className="App">
      <Home
        currentUser={currentUser}
        onLogout={handleLogout}
        onGoAdmin={currentUser.role === 'admin' ? handleGoAdmin : null}
      />
      <ThemeToggle />
    </div>
  );
}

export default App;
