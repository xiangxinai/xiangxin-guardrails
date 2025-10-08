import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/ProtectedRoute/ProtectedRoute';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import Verify from './pages/Verify/Verify';
import Dashboard from './pages/Dashboard/Dashboard';
import Results from './pages/Results/Results';
import Reports from './pages/Reports/Reports';
import Config from './pages/Config/Config';
import AdminPanel from './pages/Admin/AdminPanel';
import Account from './pages/Account/Account';
import OnlineTest from './pages/OnlineTest/OnlineTest';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify" element={<Verify />} />
      <Route path="/*" element={
        <ProtectedRoute>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/online-test" element={<OnlineTest />} />
              <Route path="/results" element={<Results />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/config/*" element={<Config />} />
              <Route path="/admin/*" element={<AdminPanel />} />
              <Route path="/account" element={<Account />} />
            </Routes>
          </Layout>
        </ProtectedRoute>
      } />
      {/* Root redirect to dashboard */}
      <Route path="/" element={<Login />} />
    </Routes>
  );
}

export default App;