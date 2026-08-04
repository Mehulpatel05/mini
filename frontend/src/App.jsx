import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Users, 
  AlertTriangle, 
  Play, 
  LogOut, 
  Search, 
  User, 
  Activity, 
  AlertOctagon, 
  Terminal, 
  CheckCircle,
  Database
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  // Authentication & Session States
  const [currentUser, setCurrentUser] = useState(null);
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  // Tab State
  const [currentTab, setCurrentTab] = useState('dashboard');

  // Application Data States
  const [users, setUsers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [selectedUserActivity, setSelectedUserActivity] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [apiStatus, setApiStatus] = useState('offline');

  // Simulator Form State
  const [simForm, setSimForm] = useState({
    user_id: '',
    name: '',
    department: '',
    role: '',
    date: new Date().toISOString().split('T')[0],
    login_time: '09:00:00',
    logout_time: '18:00:00',
    files_accessed: 'None',
    file_sensitivity: 'None',
    data_transferred_mb: 5.0,
    usb_connected: false,
    login_location: 'New York, USA',
    ip_address: '10.100.1.50',
    application_used: 'Slack'
  });
  const [simResult, setSimResult] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // 1. Initial Connection Checks and Data Fetch
  useEffect(() => {
    checkApiStatus();
    
    // Auto-refresh alerts and status every 10 seconds
    const interval = setInterval(() => {
      checkApiStatus();
      if (currentUser) {
        fetchAlerts();
      }
    }, 10000);
    
    return () => clearInterval(interval);
  }, [currentUser]);

  useEffect(() => {
    if (currentUser) {
      fetchUsers();
      fetchAlerts();
    }
  }, [currentUser]);

  useEffect(() => {
    if (selectedUserId) {
      fetchUserActivity(selectedUserId);
    }
  }, [selectedUserId]);

  const checkApiStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/`);
      if (res.ok) {
        setApiStatus('online');
      } else {
        setApiStatus('offline');
      }
    } catch {
      setApiStatus('offline');
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/users`);
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
        if (data.length > 0 && !selectedUserId) {
          setSelectedUserId(data[0].user_id);
        }
      }
    } catch (err) {
      console.error('Error fetching users:', err);
    }
  };

  const fetchUserActivity = async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/users/${id}/activity`);
      if (res.ok) {
        const data = await res.json();
        setSelectedUserActivity(data);
      }
    } catch (err) {
      console.error('Error fetching user activity:', err);
    }
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/alerts`);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (err) {
      console.error('Error fetching alerts:', err);
    }
  };

  // 2. Authentication handlers
  const handleLogin = (e) => {
    e.preventDefault();
    setLoginError('');

    if (loginUsername === 'admin' && loginPassword === 'admin') {
      setCurrentUser({ name: 'Security Admin', role: 'Admin' });
    } else if (loginUsername === 'analyst' && loginPassword === 'analyst') {
      setCurrentUser({ name: 'Security Analyst', role: 'Analyst' });
    } else {
      setLoginError('Invalid username or password. Use admin/admin or analyst/analyst.');
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setUsers([]);
    setSelectedUserId(null);
    setSelectedUserActivity(null);
    setAlerts([]);
    setLoginUsername('');
    setLoginPassword('');
  };

  // 3. Simulator Presets
  const activeUserMeta = users.find(u => u.user_id === (selectedUserId || (users[0] && users[0].user_id)));
  
  const applyPreset = (presetType) => {
    if (!activeUserMeta) return;
    
    const today = new Date().toISOString().split('T')[0];
    const dept = activeUserMeta.department;
    
    let files = "None";
    let sens = "None";
    let data = 4.2;
    let usb = false;
    let loc = "New York, USA";
    let ip = "10.100.1.50";
    let app = "Slack";
    let logTime = "09:00:00";
    let logOutTime = "18:00:00";
    
    // Geolocation helpers based on user location defaults
    if (activeUserMeta.user_id) {
      const officeIdx = (parseInt(activeUserMeta.user_id.replace('EMP', '')) % 5) + 1;
      const locations = ["New York, USA", "San Francisco, USA", "London, UK", "Bangalore, India", "Sydney, Australia"];
      loc = locations[officeIdx - 1];
      ip = `10.100.${officeIdx}.110`;
    }

    if (presetType === 'normal') {
      files = dept === 'Finance' ? 'q3_balance_sheet.xlsx' : (dept === 'R&D' ? 'main_controller.py' : 'employee_handbook.pdf');
      sens = 'internal';
      data = parseFloat((Math.random() * 15 + 1).toFixed(2));
      app = dept === 'Finance' ? 'Excel' : (dept === 'R&D' ? 'VS Code' : 'Chrome');
      logTime = "09:15:00";
      logOutTime = "10:45:00";
    } else if (presetType === 'exfil') {
      files = dept === 'Finance' ? 'payroll_salaries_2026.xlsx' : (dept === 'R&D' ? 'source_code_intellectual_property.zip' : 'employee_disciplinary_records.csv');
      sens = 'confidential';
      data = parseFloat((Math.random() * 4000 + 7500).toFixed(2));
      app = 'FileZilla';
      logTime = "02:30:00";
      logOutTime = "05:00:00";
    } else if (presetType === 'travel') {
      files = 'active_directory_master_passwords.kdbx';
      sens = 'confidential';
      data = 920.0;
      loc = 'Pyongyang, North Korea';
      ip = '175.45.176.22';
      app = 'Terminal';
      logTime = "03:15:00";
      logOutTime = "04:15:00";
    } else if (presetType === 'usb') {
      files = dept === 'R&D' ? 'source_code_intellectual_property.zip' : 'enterprise_customer_contact_list.xlsx';
      sens = 'confidential';
      data = 14500.0;
      usb = true;
      app = 'USB Mass Storage';
      logTime = "11:20:00";
      logOutTime = "12:50:00";
    }
    
    setSimForm({
      user_id: activeUserMeta.user_id,
      name: activeUserMeta.name,
      department: activeUserMeta.department,
      role: activeUserMeta.role,
      date: today,
      login_time: logTime,
      logout_time: logOutTime,
      files_accessed: files,
      file_sensitivity: sens,
      data_transferred_mb: data,
      usb_connected: usb,
      login_location: loc,
      ip_address: ip,
      application_used: app
    });
  };

  const handleSimFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSimForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleRunSimulation = async (e) => {
    e.preventDefault();
    if (currentUser.role !== 'Admin') {
      alert("Unauthorized! Only Administrators can simulate threat activities.");
      return;
    }

    setIsSimulating(true);
    setSimResult(null);

    try {
      const res = await fetch(`${API_BASE_URL}/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(simForm)
      });

      if (res.ok) {
        const data = await res.json();
        setSimResult(data.evaluation);
        // Refresh states
        fetchUsers();
        fetchAlerts();
        if (selectedUserId === simForm.user_id) {
          fetchUserActivity(selectedUserId);
        }
      } else {
        alert("Simulation failed on server side.");
      }
    } catch (err) {
      console.error(err);
      alert("Error sending simulation request to backend.");
    } finally {
      setIsSimulating(false);
    }
  };

  // 4. Data Filter
  const filteredUsers = users.filter(u => 
    u.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    u.user_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.department.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Helper to color code scores
  const getRiskColorClass = (score) => {
    if (score < 40) return 'low';
    if (score <= 70) return 'medium';
    return 'high';
  };

  // Custom Chart Tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="glass" style={{ padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}>
          <p style={{ fontSize: '12.5px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>Date: {data.date}</p>
          <p style={{ fontSize: '14px', fontWeight: 'bold', color: data.risk_score >= 70 ? 'var(--color-high)' : (data.risk_score >= 40 ? 'var(--color-medium)' : 'var(--color-low)') }}>
            Risk Score: {data.risk_score} ({data.risk_level})
          </p>
          <p style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Files Outside Role: {(data.files_outside_role_pct * 100).toFixed(1)}%</p>
          <p style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Z-Score: {data.data_transfer_zscore ? data.data_transfer_zscore.toFixed(2) : 0}</p>
        </div>
      );
    }
    return null;
  };

  // ==========================================
  // VIEW RENDER: LOGIN VIEW
  // ==========================================
  if (!currentUser) {
    return (
      <div className="login-container">
        <div className="login-background-glow"></div>
        <div className="login-card glass">
          <div className="login-logo">
            <Shield size={32} />
          </div>
          <h2>APEX SENTINEL</h2>
          <p>Insider Threat Intelligence & Monitoring</p>
          
          {loginError && <div className="login-error">{loginError}</div>}
          
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input 
                type="text" 
                className="form-input" 
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                placeholder="admin or analyst"
                required
              />
            </div>
            
            <div className="form-group">
              <label className="form-label">Password</label>
              <input 
                type="password" 
                className="form-input" 
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            
            <button type="submit" className="login-btn">Log In</button>
          </form>
          
          <div style={{ marginTop: '24px', fontSize: '12px', color: 'var(--color-text-muted)' }}>
            Admin: <code>admin/admin</code> | Analyst: <code>analyst/analyst</code>
          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // VIEW RENDER: MAIN DASHBOARD VIEW
  // ==========================================
  return (
    <div className="dashboard-layout">
      {/* Sidebar navigation */}
      <div className="sidebar glass">
        <div className="sidebar-brand">
          <Shield size={24} />
          <span>APEX SENTINEL</span>
        </div>
        
        <div className="sidebar-nav">
          <div 
            className={`nav-item ${currentTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentTab('dashboard')}
          >
            <Users size={18} />
            <span>Monitored Users</span>
          </div>

          <div 
            className={`nav-item ${currentTab === 'alerts' ? 'active' : ''}`}
            onClick={() => setCurrentTab('alerts')}
          >
            <AlertTriangle size={18} />
            <span>Alert Center ({alerts.length})</span>
          </div>

          {currentUser.role === 'Admin' && (
            <div 
              className={`nav-item ${currentTab === 'simulator' ? 'active' : ''}`}
              onClick={() => setCurrentTab('simulator')}
            >
              <Play size={18} />
              <span>Simulate Threat</span>
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="user-badge">
            <div className="user-avatar">
              <User size={18} />
            </div>
            <div className="user-info">
              <span className="user-name">{currentUser.name}</span>
              <span className="user-role">{currentUser.role}</span>
            </div>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            <LogOut size={16} />
            <span>Log Out</span>
          </button>
        </div>
      </div>

      {/* Main Content Pane */}
      <div className="main-content">
        <div className="header-container">
          <div className="page-title">
            {currentTab === 'dashboard' && (
              <>
                <h1>Employee Risk Profiles</h1>
                <p>Real-time analysis of employee behaviors and risk telemetry</p>
              </>
            )}
            {currentTab === 'alerts' && (
              <>
                <h1>Alert Management Center</h1>
                <p>Recent high-risk warning flags generated by deep neural autoencoders</p>
              </>
            )}
            {currentTab === 'simulator' && (
              <>
                <h1>Threat Scenario Simulator</h1>
                <p>Inject fake activity records to test model classification and alerts</p>
              </>
            )}
          </div>
          
          <div className="system-status">
            <div className="status-dot" style={{ backgroundColor: apiStatus === 'online' ? 'var(--color-low)' : 'var(--color-high)' }}></div>
            <span>API Status: {apiStatus.toUpperCase()}</span>
          </div>
        </div>

        {/* Dashboard Tab */}
        {currentTab === 'dashboard' && (
          <>
            {/* Top metrics grids */}
            <div className="metrics-grid">
              <div className="metric-card glow-card">
                <div className="metric-header">
                  <span>Monitored Users</span>
                  <div className="metric-icon"><Users size={16} /></div>
                </div>
                <div className="metric-value">{users.length}</div>
                <div className="metric-footer">Corporate directory index</div>
              </div>

              <div className="metric-card glow-card">
                <div className="metric-header">
                  <span>Active Alerts</span>
                  <div className="metric-icon" style={{ color: 'var(--color-high)', background: 'rgba(239, 68, 68, 0.08)' }}><AlertOctagon size={16} /></div>
                </div>
                <div className="metric-value" style={{ color: alerts.length > 0 ? 'var(--color-high)' : 'white' }}>{alerts.length}</div>
                <div className="metric-footer">Flagged high-risk events</div>
              </div>

              <div className="metric-card glow-card">
                <div className="metric-header">
                  <span>Model Baseline</span>
                  <div className="metric-icon"><Database size={16} /></div>
                </div>
                <div className="metric-value" style={{ fontSize: '20px', paddingTop: '10px' }}>Autoencoder</div>
                <div className="metric-footer">Deep Reconstruction MSE</div>
              </div>

              <div className="metric-card glow-card">
                <div className="metric-header">
                  <span>Daily Anomaly Target</span>
                  <div className="metric-icon"><Activity size={16} /></div>
                </div>
                <div className="metric-value">26.4%</div>
                <div className="metric-footer">Daily contamination baseline</div>
              </div>
            </div>

            {/* Split panel dashboard grids */}
            <div className="dashboard-panels">
              {/* Left pane: User directory list */}
              <div className="panel-card glass">
                <div className="panel-title">
                  <Users size={18} />
                  <span>Monitored Directory</span>
                </div>
                
                <div className="search-wrapper">
                  <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--color-text-muted)' }} />
                  <input 
                    type="text" 
                    className="search-input"
                    style={{ paddingLeft: '36px' }}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search users by name, ID, or department..."
                  />
                </div>

                <div className="scroll-container">
                  {filteredUsers.map((u) => {
                    // Fetch latest daily score if activity is loaded
                    const latestScore = 0.0;
                    return (
                      <div 
                        key={u.user_id} 
                        className={`user-list-item ${selectedUserId === u.user_id ? 'selected' : ''}`}
                        onClick={() => setSelectedUserId(u.user_id)}
                      >
                        <div className="user-list-meta">
                          <div className="user-list-icon">
                            {u.name.split(' ').map(n => n[0]).join('')}
                          </div>
                          <div>
                            <div className="user-list-name">{u.name}</div>
                            <div className="user-list-sub">{u.user_id} • {u.department}</div>
                          </div>
                        </div>
                        <div className="user-list-actions">
                          <span className="user-role" style={{ fontSize: '9.5px', marginRight: '10px' }}>{u.role}</span>
                        </div>
                      </div>
                    );
                  })}
                  {filteredUsers.length === 0 && (
                    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                      No users match the search terms.
                    </div>
                  )}
                </div>
              </div>

              {/* Right pane: User details panel */}
              <div className="panel-card glass">
                {selectedUserActivity ? (
                  <>
                    <div className="details-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div className="details-avatar">
                          {selectedUserActivity.metadata.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div className="details-title">
                          <h3>{selectedUserActivity.metadata.name}</h3>
                          <p>{selectedUserActivity.metadata.user_id} • {selectedUserActivity.metadata.department} ({selectedUserActivity.metadata.role})</p>
                        </div>
                      </div>
                      <button 
                        className="submit-btn" 
                        style={{ width: 'auto', marginTop: 0, padding: '8px 16px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
                        onClick={() => window.open(`${API_BASE_URL}/reports/${selectedUserId}`)}
                      >
                        <Database size={14} />
                        <span>Export PDF</span>
                      </button>
                    </div>

                    <div className="details-section-title">Risk Timeline (120 Days)</div>
                    <div className="chart-wrapper">
                      <div style={{ width: '100%', height: 200 }}>
                        <ResponsiveContainer>
                          <LineChart 
                            data={selectedUserActivity.daily_activity}
                            margin={{ top: 5, right: 5, left: -25, bottom: 5 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis 
                              dataKey="date" 
                              stroke="var(--color-text-muted)" 
                              tick={{ fontSize: 9 }}
                            />
                            <YAxis 
                              domain={[0, 100]} 
                              stroke="var(--color-text-muted)" 
                              tick={{ fontSize: 9 }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Line 
                              type="monotone" 
                              dataKey="risk_score" 
                              stroke="var(--color-primary)" 
                              strokeWidth={2}
                              dot={false}
                              activeDot={{ r: 4 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="details-section-title" style={{ marginBottom: '8px' }}>Recent Session Events</div>
                    <div className="scroll-container">
                      <div className="recent-activity-list">
                        {selectedUserActivity.raw_sessions.slice(-15).reverse().map((act, index) => (
                          <div key={index} className="activity-item">
                            <div className="activity-meta">
                              <span className="activity-file">{act.files_accessed !== 'None' ? act.files_accessed : 'No File Access'}</span>
                              <span className="activity-desc">
                                Used <strong>{act.application_used}</strong> to transfer {act.data_transferred_mb} MB from {act.login_location}
                              </span>
                            </div>
                            <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                              <span className="activity-date">{act.date} {act.login_time}</span>
                              <span className={`risk-badge ${act.is_anomaly ? 'high' : 'low'}`} style={{ fontSize: '9px', padding: '2px 4px', width: 'fit-content', marginLeft: 'auto' }}>
                                {act.is_anomaly ? 'Anomaly' : 'Normal'}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="details-empty">
                    <Activity size={48} />
                    <p>Select an employee from the Monitored Directory to view their risk analysis timeline and logs.</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Alerts Tab */}
        {currentTab === 'alerts' && (
          <div className="alerts-panel">
            {alerts.length > 0 ? (
              alerts.map((al, idx) => (
                <div key={idx} className="alert-card glass glow-card">
                  <div className="alert-main">
                    <div className="alert-icon-wrapper">
                      <AlertOctagon size={20} />
                    </div>
                    <div className="alert-details">
                      <h4>Suspicious Exfiltration Flagged for {al.name}</h4>
                      <p className="alert-description">
                        Employee <strong>{al.name}</strong> ({al.role} in {al.department}) initiated an anomalous session on <strong>{al.date}</strong>. 
                        Accessed highly sensitive file <code style={{ color: 'var(--color-primary)' }}>{al.files_accessed}</code> using <strong>{al.application_used}</strong>.
                      </p>
                      <div className="alert-indicators">
                        <div className="alert-ind-item">
                          <Terminal size={12} />
                          <span>Login Hour Dev: {al.login_hour_dev}h</span>
                        </div>
                        <div className="alert-ind-item">
                          <Activity size={12} />
                          <span>Data Transfer Z-Score: {al.data_zscore}</span>
                        </div>
                        {al.files_outside_pct > 0 && (
                          <div className="alert-ind-item" style={{ color: 'var(--color-high)' }}>
                            <AlertTriangle size={12} />
                            <span>Files Outside Dept: {(al.files_outside_pct * 100).toFixed(0)}%</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="alert-score-badge">
                    <span className="alert-timestamp">{al.alert_timestamp}</span>
                    <span className={`risk-badge ${getRiskColorClass(al.risk_score)}`} style={{ padding: '6px 12px', fontSize: '13px' }}>
                      Risk Score: {al.risk_score}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '80px', textAlign: 'center', color: 'var(--color-text-muted)' }} className="glass">
                <CheckCircle size={48} style={{ color: 'var(--color-low)', marginBottom: '16px' }} />
                <h3>No Alerts Triggered</h3>
                <p style={{ marginTop: '8px' }}>Autoencoder model indicates system activity is within normal baseline parameters.</p>
              </div>
            )}
          </div>
        )}

        {/* Simulator Tab */}
        {currentTab === 'simulator' && (
          <div className="simulation-grid">
            {/* Left Col: Setup form */}
            <div className="panel-card glass" style={{ height: 'auto' }}>
              <div className="panel-title">
                <Play size={18} />
                <span>Simulation Dashboard</span>
              </div>
              
              <div className="preset-container">
                <span className="form-label">Simulation Presets</span>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <button className="preset-btn" onClick={() => applyPreset('normal')}>
                    <div>
                      <div className="preset-title">Normal Shift Check-in</div>
                      <div className="preset-desc">Typical daytime file edits</div>
                    </div>
                    <span className="preset-badge normal">Normal</span>
                  </button>

                  <button className="preset-btn" onClick={() => applyPreset('exfil')}>
                    <div>
                      <div className="preset-title">Late-Night Exfil</div>
                      <div className="preset-desc">Odd-hour massive download</div>
                    </div>
                    <span className="preset-badge anomalous">Anomalous</span>
                  </button>

                  <button className="preset-btn" onClick={() => applyPreset('travel')}>
                    <div>
                      <div className="preset-title">Travel Anomaly</div>
                      <div className="preset-desc">Credential abuse from overseas</div>
                    </div>
                    <span className="preset-badge anomalous">Anomalous</span>
                  </button>

                  <button className="preset-btn" onClick={() => applyPreset('usb')}>
                    <div>
                      <div className="preset-title">Resignation USB Copy</div>
                      <div className="preset-desc">Proprietary copy to USB</div>
                    </div>
                    <span className="preset-badge anomalous">Anomalous</span>
                  </button>
                </div>
              </div>

              <form onSubmit={handleRunSimulation}>
                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">User ID</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="user_id"
                      value={simForm.user_id}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Employee Name</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="name"
                      value={simForm.name}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Department</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="department"
                      value={simForm.department}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Role</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="role"
                      value={simForm.role}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Date</label>
                    <input 
                      type="date" 
                      className="form-input" 
                      name="date"
                      value={simForm.date}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Application Used</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="application_used"
                      value={simForm.application_used}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Login Time</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="login_time"
                      value={simForm.login_time}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Logout Time</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="logout_time"
                      value={simForm.logout_time}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">File Accessed</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="files_accessed"
                      value={simForm.files_accessed}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">File Sensitivity</label>
                    <select 
                      className="form-input"
                      name="file_sensitivity"
                      value={simForm.file_sensitivity}
                      onChange={handleSimFormChange}
                    >
                      <option value="None">None</option>
                      <option value="public">Public</option>
                      <option value="internal">Internal</option>
                      <option value="confidential">Confidential</option>
                    </select>
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Data Transferred (MB)</label>
                    <input 
                      type="number" 
                      step="0.01"
                      className="form-input" 
                      name="data_transferred_mb"
                      value={simForm.data_transferred_mb}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Suspicious Location</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="login_location"
                      value={simForm.login_location}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">IP Address</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      name="ip_address"
                      value={simForm.ip_address}
                      onChange={handleSimFormChange}
                      required 
                    />
                  </div>

                  <div className="form-group" style={{ display: 'flex', alignItems: 'center', height: '100%', paddingTop: '20px' }}>
                    <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', marginBottom: 0 }}>
                      <input 
                        type="checkbox" 
                        name="usb_connected"
                        checked={simForm.usb_connected}
                        onChange={handleSimFormChange}
                        style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                      />
                      <span>USB Device Connected</span>
                    </label>
                  </div>
                </div>

                <button type="submit" className="submit-btn" disabled={isSimulating}>
                  {isSimulating ? 'Injecting telemetry...' : 'Execute Simulator Injection'}
                </button>
              </form>
            </div>

            {/* Right Col: Simulation response details */}
            <div className="panel-card glass" style={{ height: 'fit-content' }}>
              <div className="panel-title">
                <Activity size={18} />
                <span>Simulation Results</span>
              </div>

              {simResult ? (
                <div className="sim-result-card glow-card">
                  <div className="sim-result-header">
                    <div>
                      <h3 style={{ fontSize: '18px', color: 'white' }}>Risk Evaluation Complete</h3>
                      <p style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Daily features recomputed dynamically</p>
                    </div>
                    <span className={`risk-badge ${getRiskColorClass(simResult.risk_score)}`} style={{ padding: '8px 16px', fontSize: '15px' }}>
                      {simResult.risk_level} ({simResult.risk_score})
                    </span>
                  </div>

                  {simResult.alert_triggered && (
                    <div className="alert-card" style={{ marginBottom: '24px', background: 'rgba(239,68,68,0.05)' }}>
                      <div className="alert-main">
                        <div className="alert-icon-wrapper">
                          <AlertTriangle size={18} />
                        </div>
                        <div className="alert-details">
                          <h4 style={{ color: 'var(--color-high)' }}>ALERT TRIGGERED</h4>
                          <p className="alert-description" style={{ fontSize: '12.5px', marginTop: '2px' }}>
                            Reconstruction error crossed normal baseline limits. High risk incident successfully logged.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="details-section-title">Recomputed Feature Vector</div>
                  <div className="sim-features-grid">
                    <div className="sim-feat-item">
                      <span className="sim-feat-label">Login Hour Deviation</span>
                      <span className="sim-feat-val">{simResult.features.login_hour_deviation.toFixed(3)}h</span>
                    </div>

                    <div className="sim-feat-item">
                      <span className="sim-feat-label">Data Transfer Z-Score</span>
                      <span className="sim-feat-val">{simResult.features.data_transfer_zscore.toFixed(3)}</span>
                    </div>

                    <div className="sim-feat-item">
                      <span className="sim-feat-label">Weekend Access</span>
                      <span className="sim-feat-val">{simResult.features.is_weekend_access === 1 ? 'Yes' : 'No'}</span>
                    </div>

                    <div className="sim-feat-item">
                      <span className="sim-feat-label">Files Outside Dept Pct</span>
                      <span className="sim-feat-val">{(simResult.features.files_outside_role_pct * 100).toFixed(1)}%</span>
                    </div>

                    <div className="sim-feat-item">
                      <span className="sim-feat-label">USB 7-Day Frequency</span>
                      <span className="sim-feat-val">{simResult.features.usb_freq_7day} connections</span>
                    </div>

                    <div className="sim-feat-item">
                      <span className="sim-feat-label">Distinct Geocodes (7d)</span>
                      <span className="sim-feat-val">{simResult.features.distinct_locations_7day} unique locations</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ padding: '60px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                  <Play size={40} style={{ marginBottom: '12px' }} />
                  <p>Execute an injection simulation to see computed features and autoencoder risk tiering results.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
