const API_BASE = 'http://127.0.0.1:8000';

let students = [];
let alerts = [];
let warnings = [];
let chalans = [];
let previousAlertCount = 0;
let audioCtx = null;

// ---------------- Alert Beep Sound ----------------
function playBeep() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.type = 'square';
    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    osc.start();
    osc.frequency.setValueAtTime(660, audioCtx.currentTime + 0.15);
    osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.3);
    osc.stop(audioCtx.currentTime + 0.5);
  } catch (_) {}
}

// ---------------- Browser Notifications ----------------
function requestNotificationPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

function showBrowserNotification(title, body) {
  if ('Notification' in window && Notification.permission === 'granted') {
    try { new Notification(title, { body, icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🚨</text></svg>' }); } catch (_) {}
  }
}

// ---------------- Navigation ----------------
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const tab = link.dataset.tab;
    switchTab(tab);
  });
});

document.querySelectorAll('.sub-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const group = tab.parentElement;
    group.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    document.querySelectorAll('.sub-content').forEach(c => c.classList.remove('active'));
    document.getElementById(tab.dataset.subtab).classList.add('active');
  });
});

function switchTab(tab) {
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  document.querySelector(`.nav-link[data-tab="${tab}"]`)?.classList.add('active');

  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById(tab).classList.add('active');

  const titles = {
    dashboard: 'Dashboard',
    alerts: 'Live Alerts',
    cameras: 'Cameras',
    students: 'Students',
    chalans: 'Warnings & Chalans',
    settings: 'Settings',
  };
  document.getElementById('pageTitle').textContent = titles[tab];

  if (tab === 'alerts') loadAlerts();
  if (tab === 'students') loadStudents();
  if (tab === 'chalans') loadWarningsAndChalans();
  if (tab === 'dashboard') refreshDashboard();
}

// ---------------- API Helpers ----------------
async function apiGet(path) {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(res.statusText);
    return await res.json();
  } catch (err) {
    console.error('API GET error:', err);
    return null;
  }
}

async function apiPost(path, body) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || res.statusText);
    return data;
  } catch (err) {
    console.error('API POST error:', err);
    showToast(err.message, 'error');
    return null;
  }
}

async function apiPatch(path, body) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || res.statusText);
    return data;
  } catch (err) {
    console.error('API PATCH error:', err);
    showToast(err.message, 'error');
    return null;
  }
}

// ---------------- Dashboard ----------------
async function refreshDashboard() {
  const [status, alertsData, studentsData, warningsData, chalansData] = await Promise.all([
    apiGet('/'),
    apiGet('/alerts'),
    apiGet('/admin/students'),
    apiGet('/admin/warnings'),
    apiGet('/admin/chalans'),
  ]);

  if (alertsData) {
    document.getElementById('dashAlerts').textContent = alertsData.count || 0;
    document.getElementById('navAlertCount').textContent = alertsData.count || 0;

    const newCount = alertsData.count || 0;
    if (previousAlertCount > 0 && newCount > previousAlertCount) {
      const diff = newCount - previousAlertCount;
      const freshAlerts = (alertsData.alerts || []).slice(0, diff);
      for (const a of freshAlerts) {
        playBeep();
        const label = a.type === 'smoking' ? 'Smoking Detected' : 'ID Card Missing';
        showBrowserNotification(label, `${a.camera} at ${a.timestamp_iso}`);
      }
    }
    previousAlertCount = newCount;
  }
  if (studentsData) document.getElementById('dashStudents').textContent = studentsData.students.length;
  if (warningsData) document.getElementById('dashWarnings').textContent = warningsData.warnings.length;
  if (chalansData) document.getElementById('dashChalans').textContent = chalansData.chalans.length;

  renderRecentAlerts(alertsData?.alerts?.slice(0, 5) || []);
  renderCameraStatus(status?.cameras || {});
}

function renderRecentAlerts(items) {
  const container = document.getElementById('recentAlerts');
  if (!items.length) {
    container.innerHTML = '<div class="empty-state">No recent alerts</div>';
    return;
  }
  container.innerHTML = items.map(a => `
    <div class="alert-item">
      <img class="alert-thumb" src="${API_BASE}/alert_image/${a.image}" alt="" onerror="this.src=''" />
      <div class="alert-info">
        <p>${a.type === 'smoking' ? 'Smoking Detected' : 'ID Card Missing'}</p>
        <span>${a.camera} &bull; ${a.timestamp_iso}</span>
      </div>
      <span class="alert-tag ${a.type === 'smoking' ? 'tag-smoking' : 'tag-id'}">${a.type}</span>
    </div>
  `).join('');
}

function renderCameraStatus(cameras) {
  const container = document.getElementById('cameraStatusList');
  const entries = Object.entries(cameras);
  if (!entries.length) {
    container.innerHTML = '<div class="empty-state">No cameras configured</div>';
    return;
  }
  container.innerHTML = entries.map(([name, online]) => `
    <div class="alert-item" style="justify-content: space-between;">
      <div style="display:flex; align-items:center; gap:12px;">
        <svg width="22" height="22" fill="${online ? 'var(--success)' : 'var(--danger)'}" viewBox="0 0 24 24"><path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/></svg>
        <div>
          <p style="margin:0; font-weight:600; text-transform:capitalize;">${name}</p>
          <span style="font-size:12px; color:var(--text-muted);">Source ${name === 'classroom' ? 0 : 1}</span>
        </div>
      </div>
      <span class="status-pill ${online ? 'online' : 'offline'}"><span class="dot"></span> ${online ? 'Online' : 'Offline'}</span>
    </div>
  `).join('');
}

// ---------------- Alerts ----------------
async function loadAlerts() {
  const data = await apiGet('/alerts');
  if (!data) return;
  const newAlerts = data.alerts || [];
  const newCount = data.count || 0;

  if (previousAlertCount > 0 && newCount > previousAlertCount) {
    const diff = newCount - previousAlertCount;
    const freshAlerts = newAlerts.slice(0, diff);
    for (const a of freshAlerts) {
      playBeep();
      const label = a.type === 'smoking' ? 'Smoking Detected' : 'ID Card Missing';
      showBrowserNotification(label, `${a.camera} at ${a.timestamp_iso}`);
    }
  }
  previousAlertCount = newCount;

  alerts = newAlerts;
  document.getElementById('navAlertCount').textContent = newCount;
  renderAlerts();
}

function renderAlerts() {
  const grid = document.getElementById('alertsGrid');
  if (!alerts.length) {
    grid.innerHTML = '<div class="empty-state">No active alerts</div>';
    return;
  }
  grid.innerHTML = alerts.map(a => `
    <div class="alert-card">
      <div class="alert-card-header">
        <div class="icon">
          <svg viewBox="0 0 24 24"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
        </div>
        <div>
          <h4>${a.type === 'smoking' ? 'Smoking Detected' : 'ID Card Missing'}</h4>
          <span>${a.camera} &bull; ${a.timestamp_iso}</span>
        </div>
        <span class="alert-tag ${a.type === 'smoking' ? 'tag-smoking' : 'tag-id'}">${a.type}</span>
      </div>
      <img class="alert-card-image" src="${API_BASE}/alert_image/${a.image}" alt="Detection snapshot" onerror="this.style.display='none'" />
      <div class="alert-card-body">
        <div class="alert-meta">
          <span>Confidence: ${(a.confidence * 100).toFixed(1)}%</span>
          <span>Alert ID: ${a.id}</span>
        </div>
        <div class="alert-actions">
          <button class="btn btn-warning" onclick="openActionModal('warning', '${a.id}', '${a.camera}')">Send Warning</button>
          <button class="btn btn-danger" onclick="openActionModal('chalan', '${a.id}', '${a.camera}')">Issue Chalan</button>
        </div>
      </div>
    </div>
  `).join('');
}

// ---------------- Students ----------------
async function loadStudents() {
  const data = await apiGet('/admin/students');
  if (!data) return;
  students = data.students || [];
  renderStudents();
}

function renderStudents() {
  const tbody = document.getElementById('studentsTableBody');
  if (!students.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">No students found. Add one to get started.</td></tr>';
    return;
  }
  tbody.innerHTML = students.map(s => `
    <tr>
      <td><strong>${s.name}</strong></td>
      <td>${s.roll_no}</td>
      <td>${s.department || '-'}</td>
      <td>${s.email || '-'}</td>
      <td><span class="alert-tag tag-id">${s.warnings_count}</span></td>
      <td><span class="alert-tag tag-smoking">${s.chalans_count}</span></td>
      <td>
        <button class="btn btn-ghost btn-sm" onclick="openActionModal('warning', '', 'classroom', ${s.id})">Warn</button>
        <button class="btn btn-danger btn-sm" onclick="openActionModal('chalan', '', 'classroom', ${s.id})">Chalan</button>
      </td>
    </tr>
  `).join('');
}

async function saveStudent() {
  const name = document.getElementById('studentName').value.trim();
  const roll_no = document.getElementById('studentRoll').value.trim();
  const department = document.getElementById('studentDept').value.trim();
  const email = document.getElementById('studentEmail').value.trim();

  if (!name || !roll_no) {
    showToast('Name and Roll Number are required', 'error');
    return;
  }

  const res = await apiPost('/admin/students', { name, roll_no, department, email });
  if (res) {
    showToast('Student added successfully');
    closeStudentModal();
    loadStudents();
  }
}

// ---------------- Warnings & Chalans ----------------
async function loadWarningsAndChalans() {
  const [w, c] = await Promise.all([
    apiGet('/admin/warnings'),
    apiGet('/admin/chalans'),
  ]);
  if (w) warnings = w.warnings || [];
  if (c) chalans = c.chalans || [];
  renderWarnings();
  renderChalans();
}

function renderWarnings() {
  const tbody = document.getElementById('warningsTableBody');
  if (!warnings.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-cell">No warnings sent yet</td></tr>';
    return;
  }
  tbody.innerHTML = warnings.map(w => `
    <tr>
      <td>${w.created_at}</td>
      <td><strong>${w.student_name}</strong><br><small>${w.roll_no}</small></td>
      <td>${w.camera || '-'}</td>
      <td>${w.message}</td>
      <td>${w.sent_email ? '<span class="status-pill online">Yes</span>' : '<span class="status-pill offline">No</span>'}</td>
      <td>${w.sent_portal ? '<span class="status-pill online">Yes</span>' : '<span class="status-pill offline">No</span>'}</td>
    </tr>
  `).join('');
}

function renderChalans() {
  const tbody = document.getElementById('chalansTableBody');
  if (!chalans.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">No chalans issued yet</td></tr>';
    return;
  }
  tbody.innerHTML = chalans.map(c => `
    <tr>
      <td>${c.created_at}</td>
      <td><strong>${c.student_name}</strong><br><small>${c.roll_no}</small></td>
      <td>Rs. ${c.amount}</td>
      <td>${c.reason}</td>
      <td>${c.due_date}</td>
      <td><span class="status-pill ${c.status === 'paid' ? 'online' : 'offline'}">${c.status}</span></td>
      <td>Email: ${c.sent_email ? 'Yes' : 'No'}<br>Portal: ${c.sent_portal ? 'Yes' : 'No'}</td>
    </tr>
  `).join('');
}

// ---------------- Action Modal ----------------
function resetActionDeliveryStatus() {
  const status = document.getElementById('actionDeliveryStatus');
  status.textContent = '';
  status.className = 'action-delivery-status';
  status.hidden = true;
}

function showActionDeliveryStatus(message, type = 'error') {
  const status = document.getElementById('actionDeliveryStatus');
  status.textContent = message;
  status.className = `action-delivery-status ${type}`;
  status.hidden = false;
}

function setActionControlsDisabled(disabled) {
  const type = document.getElementById('actionType').value;
  const confirmButton = document.getElementById('actionConfirmBtn');
  const controls = [
    document.getElementById('actionCloseBtn'),
    document.getElementById('actionCancelBtn'),
    confirmButton,
    document.getElementById('actionStudent'),
    document.getElementById('actionReason'),
    document.getElementById('sendPortal'),
    document.getElementById('sendEmail'),
  ];

  controls.forEach(control => {
    control.disabled = disabled;
  });
  confirmButton.textContent = disabled ? 'Sending…' : (type === 'warning' ? 'Send Warning' : 'Issue Chalan');
}

function getApiErrorMessage(data, status) {
  if (typeof data?.detail === 'string') return data.detail;
  if (Array.isArray(data?.detail)) return data.detail.map(item => item.msg).join(', ');
  if (typeof data?.error === 'string') return data.error;
  return `Request failed (${status})`;
}

function renderDeliveryStatus(result) {
  const delivery = result.delivery || {};
  const lines = Object.entries(delivery)
    .filter(([, outcome]) => outcome.requested)
    .map(([channel, outcome]) => {
      const label = channel === 'email' ? 'Email' : 'Portal';
      const outcomeText = outcome.sent ? 'sent' : 'failed';
      return `${label}: ${outcomeText}${outcome.error ? ` - ${outcome.error}` : ''}`;
    });

  if (!lines.length) {
    showActionDeliveryStatus('No delivery outcome was returned.', 'error');
    return;
  }

  const allDelivered = result.success === true;
  const heading = allDelivered ? 'Delivery completed:' : 'Delivery incomplete:';
  showActionDeliveryStatus(`${heading}\n${lines.join('\n')}`, allDelivered ? 'success' : 'error');
}

function openActionModal(type, alertId, camera, preselectedStudentId) {
  document.getElementById('actionType').value = type;
  document.getElementById('actionAlertId').value = alertId;
  document.getElementById('actionCamera').value = camera;
  document.getElementById('actionModalTitle').textContent = type === 'warning' ? 'Send Warning' : 'Issue Chalan';

  const reasonInput = document.getElementById('actionReason');
  reasonInput.value = type === 'warning'
    ? 'Smoking detected on campus premises'
    : 'Repeated smoking violation despite prior warning';

  const select = document.getElementById('actionStudent');
  select.innerHTML = students.map(s =>
    `<option value="${s.id}" ${s.id === preselectedStudentId ? 'selected' : ''}>${s.name} (${s.roll_no})</option>`
  ).join('');

  document.getElementById('sendPortal').checked = true;
  document.getElementById('sendEmail').checked = false;
  document.getElementById('actionEvidenceNote').hidden = Boolean(alertId);
  resetActionDeliveryStatus();
  setActionControlsDisabled(false);

  document.getElementById('actionModal').classList.add('show');
}

function closeActionModal() {
  if (document.getElementById('actionConfirmBtn').disabled) return;
  document.getElementById('actionModal').classList.remove('show');
}

async function confirmAction() {
  const type = document.getElementById('actionType').value;
  const studentId = parseInt(document.getElementById('actionStudent').value, 10);
  const alertId = document.getElementById('actionAlertId').value;
  const camera = document.getElementById('actionCamera').value;
  const reason = document.getElementById('actionReason').value;
  const sendEmail = document.getElementById('sendEmail').checked;
  const sendPortal = document.getElementById('sendPortal').checked;

  if (!sendEmail && !sendPortal) {
    const message = 'Select at least one delivery method (Email or Portal)';
    showActionDeliveryStatus(message);
    showToast(message, 'error');
    return;
  }

  if (Number.isNaN(studentId)) {
    const message = 'Select a student before sending';
    showActionDeliveryStatus(message);
    showToast(message, 'error');
    return;
  }

  const payload = {
    student_id: studentId,
    alert_id: alertId,
    camera: camera || 'classroom',
    reason,
    send_email: sendEmail,
    send_portal: sendPortal,
  };

  const endpoint = type === 'warning' ? '/admin/send_warning' : '/admin/issue_chalan';
  const actionLabel = type === 'warning' ? 'Warning' : 'Chalan';
  let closeAfterSuccess = false;

  setActionControlsDisabled(true);
  resetActionDeliveryStatus();

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const result = await response.json().catch(() => ({}));

    if (!response.ok) {
      const message = getApiErrorMessage(result, response.status);
      showActionDeliveryStatus(message);
      showToast(message, 'error');
      return;
    }

    renderDeliveryStatus(result);
    if (!result.success) {
      showToast(`${actionLabel} was not delivered to every selected channel`, 'error');
      return;
    }

    closeAfterSuccess = true;
    showToast(type === 'warning' ? 'Warning sent successfully' : 'Chalan issued successfully');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Network request failed';
    showActionDeliveryStatus(message);
    showToast(message, 'error');
  } finally {
    setActionControlsDisabled(false);
    if (closeAfterSuccess) {
      closeActionModal();
      loadWarningsAndChalans();
      refreshDashboard();
    }
  }
}

// ---------------- Student Modal ----------------
function openStudentModal() {
  document.getElementById('studentName').value = '';
  document.getElementById('studentRoll').value = '';
  document.getElementById('studentDept').value = '';
  document.getElementById('studentEmail').value = '';
  document.getElementById('studentModal').classList.add('show');
}

function closeStudentModal() {
  document.getElementById('studentModal').classList.remove('show');
}

// ---------------- Toast ----------------
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.style.background = type === 'error' ? 'var(--danger)' : 'var(--success)';
  toast.classList.add('show');
  clearTimeout(toast.hideTimeout);
  toast.hideTimeout = setTimeout(
    () => toast.classList.remove('show'),
    type === 'error' ? 7000 : 3000,
  );
}

// ---------------- Init ----------------
document.getElementById('refreshBtn').addEventListener('click', () => {
  const activeTab = document.querySelector('.tab-content.active')?.id;
  if (activeTab === 'dashboard') refreshDashboard();
  if (activeTab === 'alerts') loadAlerts();
  if (activeTab === 'students') loadStudents();
  if (activeTab === 'chalans') loadWarningsAndChalans();
});

window.addEventListener('DOMContentLoaded', () => {
  requestNotificationPermission();
  refreshDashboard();
  loadStudents();
  setInterval(() => {
    const activeTab = document.querySelector('.tab-content.active')?.id;
    if (activeTab === 'dashboard') refreshDashboard();
    if (activeTab === 'alerts') loadAlerts();
  }, 4000);
});

window.openStudentModal = openStudentModal;
window.closeStudentModal = closeStudentModal;
window.saveStudent = saveStudent;
window.openActionModal = openActionModal;
window.closeActionModal = closeActionModal;
window.confirmAction = confirmAction;
window.loadAlerts = loadAlerts;
