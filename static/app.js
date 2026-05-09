const $ = (id) => document.getElementById(id);

function fmtBytes(v) {
  if (!v) return '0 B';
  const units = ['B','KB','MB','GB'];
  let i = 0;
  let n = v;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i += 1;
  }
  return `${n.toFixed(n < 10 && i > 0 ? 1 : 0)} ${units[i]}`;
}

function setDot(id, ok) {
  $(id).classList.toggle('ok', !!ok);
}

function logActivity(title, payload) {
  const stamp = new Date().toISOString();
  const body = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
  $('activityLog').textContent = `[${stamp}] ${title}\n${body}\n\n` + $('activityLog').textContent;
}

async function postJson(url) {
  const r = await fetch(url, { method: 'POST' });
  const j = await r.json();
  logActivity(url, j);
  await refreshStatus();
  return j;
}

async function deletePcap(name) {
  const r = await fetch(`/api/pcap/${encodeURIComponent(name)}`, { method: 'DELETE' });
  const j = await r.json();
  logActivity(`delete ${name}`, j);
  await refreshStatus();
  return j;
}

function renderPcaps(pcaps) {
  const root = $('pcapList');
  if (!pcaps.length) {
    root.innerHTML = '<div class="quiet">No PCAPs saved yet.</div>';
    return;
  }
  root.innerHTML = pcaps.map(p => `
    <div class="download-item">
      <div class="download-meta">
        <strong>${p.name}</strong>
        <span class="quiet">${fmtBytes(p.size)} • ${p.mtime}</span>
      </div>
      <div class="download-actions">
        <a href="/download/${encodeURIComponent(p.name)}">Download</a>
        <button class="danger small-button delete-pcap" data-name="${p.name}">Delete</button>
      </div>
    </div>
  `).join('');
}

async function refreshStatus() {
  const r = await fetch('/api/status');
  const s = await r.json();
  setDot('server8888Dot', s.server_listening_8888);
  setDot('server1080Dot', s.server_listening_1080);
  setDot('tunnelDot', s.tunnel_connected);
  $('capturePill').textContent = s.capture_running ? 'Capture: running' : 'Capture: idle';
  $('captureFile').textContent = s.capture_file || '—';
  $('captureSize').textContent = fmtBytes(s.capture_size || 0);
  $('serverLog').textContent = s.server_log || 'No server log yet.';
  $('clientLog').textContent = s.client_log || 'No client log yet.';
  $('captureLog').textContent = s.capture_log || 'No capture log yet.';
  $('ewHash').textContent = s.ew_hash || 'Not available';
  $('ewFile').textContent = s.ew_file || 'Not available';
  $('ewStrings').textContent = s.ew_strings_head || 'Not available';
  renderPcaps(s.pcaps || []);
}

document.querySelectorAll('button[data-action]').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const prev = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Working…';
    try {
      const action = btn.dataset.action;
      const map = {
        'init': '/api/init',
        'lab-reset': '/api/lab/reset',
        'server-start': '/api/server/start',
        'server-reset': '/api/server/reset',
        'client-connect': '/api/client/connect',
        'client-reset': '/api/client/reset',
        'capture-start': '/api/capture/start',
        'capture-stop': '/api/capture/stop',
        'test-socks': '/api/test/socks',
        'test-ping': '/api/test/ping',
      };
      await postJson(map[action]);
    } catch (e) {
      logActivity('error', String(e));
    } finally {
      btn.disabled = false;
      btn.textContent = prev;
    }
  });
});

document.addEventListener('click', async (event) => {
  const btn = event.target.closest('.delete-pcap');
  if (!btn) return;
  const name = btn.dataset.name;
  if (!confirm(`Delete ${name}?`)) return;
  const prev = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Deleting…';
  try {
    await deletePcap(name);
  } catch (e) {
    logActivity('error', String(e));
  } finally {
    btn.disabled = false;
    btn.textContent = prev;
  }
});

refreshStatus();
setInterval(refreshStatus, 4000);
