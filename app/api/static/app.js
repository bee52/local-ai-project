const questionForm = document.querySelector('#query-form');
const ingestForm = document.querySelector('#ingest-form');
const answerBody = document.querySelector('#answer-body');
const sourcesList = document.querySelector('#sources-list');
const sourceCount = document.querySelector('#source-count');
const requestState = document.querySelector('#request-state');
const systemState = document.querySelector('#system-state');
const jobList = document.querySelector('#job-list');
const jobs = new Map();

async function request(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || payload.error || `Request failed (${response.status})`);
  return payload;
}

function setRequestState(label, busy = false) {
  requestState.textContent = label;
  requestState.style.color = busy ? 'var(--orange)' : 'var(--acid)';
}

function renderSources(citations = [], results = []) {
  sourceCount.textContent = citations.length;
  if (!citations.length) {
    sourcesList.innerHTML = '<p class="empty-state">No sources returned.</p>';
    return;
  }
  sourcesList.innerHTML = citations.map((citation, index) => {
    const result = results[index] || {};
    const score = citation.score == null ? '—' : Number(citation.score).toFixed(3);
    return `<article class="source-card"><div class="source-top"><span>${String(index + 1).padStart(2, '0')} / ${escapeHtml(result.strategy || 'source')}</span><span>${score}</span></div><div class="source-name">${escapeHtml(citation.source || 'unknown source')}</div><p>${escapeHtml(result.text || '')}</p></article>`;
  }).join('');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

questionForm.addEventListener('submit', async event => {
  event.preventDefault();
  const question = document.querySelector('#question').value.trim();
  if (!question) return;
  setRequestState('working', true);
  answerBody.innerHTML = '<p class="empty-state">Searching the corpus...</p>';
  sourcesList.innerHTML = '<p class="empty-state">Retrieving passages...</p>';
  try {
    const payload = { question, limit: Number(document.querySelector('#limit').value), use_hybrid: document.querySelector('#hybrid').checked, use_reranking: document.querySelector('#reranking').checked, use_hyde: document.querySelector('#hyde').checked };
    const [search, answer] = await Promise.all([
      request('/search', { method: 'POST', body: JSON.stringify(payload) }),
      request('/query', { method: 'POST', body: JSON.stringify(payload) })
    ]);
    answerBody.innerHTML = `<p class="answer-text">${escapeHtml(answer.answer || 'No answer returned.')}</p>`;
    renderSources(search.citations, search.results);
    setRequestState('complete');
  } catch (error) {
    answerBody.innerHTML = `<p class="empty-state">${escapeHtml(error.message)}</p>`;
    sourcesList.innerHTML = '<p class="empty-state">Sources unavailable.</p>';
    setRequestState('error');
  }
});

ingestForm.addEventListener('submit', async event => {
  event.preventDefault();
  const source = document.querySelector('#source-path').value.trim();
  if (!source) return;
  const button = ingestForm.querySelector('button');
  button.disabled = true;
  button.textContent = 'Queuing...';
  try {
    const job = await request('/documents/ingest', { method: 'POST', body: JSON.stringify({ source }) });
    jobs.set(job.job_id, job);
    renderJobs();
    pollJob(job.job_id);
    document.querySelector('#source-path').value = '';
  } catch (error) {
    jobs.set(`error-${Date.now()}`, { status: 'failed', error: error.message, operation: 'ingest_document' });
    renderJobs();
  } finally {
    button.disabled = false;
    button.innerHTML = 'Queue ingestion <span>↗</span>';
  }
});

function renderJobs() {
  jobList.innerHTML = [...jobs.values()].slice(-4).reverse().map(job => `<div class="job"><span>${escapeHtml(job.operation || 'ingestion')}</span><span class="job-status ${job.status === 'failed' ? 'failed' : ''}">${escapeHtml(job.status)}${job.error ? ` · ${escapeHtml(job.error)}` : ''}</span></div>`).join('');
}

async function pollJob(jobId) {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 400));
    try {
      const job = await request(`/jobs/${jobId}`);
      jobs.set(jobId, job);
      renderJobs();
      if (['completed', 'failed'].includes(job.status)) return;
    } catch (_) { return; }
  }
}

async function checkSystem() {
  try {
    const health = await request('/health/ready');
    systemState.classList.toggle('offline', !health.healthy);
    systemState.innerHTML = `<span class="state-dot"></span>${health.healthy ? 'system ready' : 'dependencies offline'}`;
  } catch (_) {
    systemState.classList.add('offline');
    systemState.innerHTML = '<span class="state-dot"></span>api unavailable';
  }
}

checkSystem();
