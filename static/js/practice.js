// PrepTrack — practice editor: CodeMirror setup + Run / Submit wiring

let editor = null;

(function initEditor() {
  const textarea = document.getElementById('codeEditor');
  if (!textarea || typeof CodeMirror === 'undefined') {
    console.error('CodeMirror failed to load — check static/js/vendor/codemirror/ files are present.');
    return;
  }

  editor = CodeMirror.fromTextArea(textarea, {
    mode: 'python',
    theme: 'dracula',
    lineNumbers: true,
    indentUnit: 4,
    tabSize: 4,
    matchBrackets: true,
    viewportMargin: Infinity,
  });
})();

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str == null ? '' : str;
  return div.innerHTML;
}

function setOutputLoading(label) {
  const panel = document.getElementById('outputPanel');
  panel.innerHTML = `<div style="color: var(--text-faint); font-size: 13px;">${label}…</div>`;
}

function renderRunResult(result) {
  const panel = document.getElementById('outputPanel');
  if (result.error) {
    panel.innerHTML = `<div class="verdict runtime-error">Error</div><pre style="background:var(--bg-inset); padding:10px; border-radius:3px; white-space:pre-wrap;">${escapeHtml(result.error)}</pre>`;
    return;
  }

  let html = '';
  if (result.timed_out) {
    html += `<div class="verdict time-limit-exceeded">Time limit exceeded</div>`;
  } else if (result.stderr && result.stderr.trim()) {
    html += `<div class="verdict runtime-error">Runtime error</div>
      <pre style="background:var(--bg-inset); padding:10px; border-radius:3px; white-space:pre-wrap; color:#e6667a;">${escapeHtml(result.stderr)}</pre>`;
  } else {
    html += `<div class="verdict accepted">Ran successfully</div>`;
  }
  html += `<div class="tc-label" style="margin-top:8px;">stdout</div><pre>${escapeHtml(result.stdout) || '(empty)'}</pre>`;
  panel.innerHTML = html;
}

function statusClass(status) {
  return {
    'Accepted': 'accepted',
    'Wrong Answer': 'wrong-answer',
    'Runtime Error': 'runtime-error',
    'Time Limit Exceeded': 'time-limit-exceeded',
  }[status] || '';
}

function renderSubmitResult(result) {
  const panel = document.getElementById('outputPanel');
  if (result.error) {
    panel.innerHTML = `<div class="verdict runtime-error">Error</div><pre>${escapeHtml(result.error)}</pre>`;
    return;
  }

  let html = `<div class="verdict ${statusClass(result.status)}">${result.status} — ${result.passed}/${result.total} test cases passed</div>`;

  result.results.forEach((r, i) => {
    const cls = r.passed ? 'pass' : 'fail';
    const visible = r.is_sample || !r.passed; // always show sample cases + any failing case
    if (!visible) return;
    html += `<div class="test-case ${cls}">
      <div class="tc-label">${r.is_sample ? 'Sample' : 'Hidden'} case ${i + 1} — ${r.passed ? 'Passed' : 'Failed'}</div>
      <div class="tc-label">Input</div><pre>${escapeHtml(r.input)}</pre>
      <div class="tc-label">Expected</div><pre>${escapeHtml(r.expected)}</pre>
      <div class="tc-label">Got</div><pre>${escapeHtml(r.actual) || '(empty)'}</pre>
      ${r.stderr ? `<div class="tc-label">stderr</div><pre style="color:#e6667a;">${escapeHtml(r.stderr)}</pre>` : ''}
    </div>`;
  });

  const hiddenPassedCount = result.results.filter(r => !r.is_sample && r.passed).length;
  const hiddenTotal = result.results.filter(r => !r.is_sample).length;
  if (hiddenTotal > 0) {
    html += `<div style="font-size:12px; color:var(--text-faint); margin-top:6px;">
      ${hiddenPassedCount}/${hiddenTotal} additional hidden case(s) passed.</div>`;
  }

  panel.innerHTML = html;

  if (result.status === 'Accepted') {
    showSolvedBanner();
  }
}

function showSolvedBanner() {
  const banner = document.getElementById('solvedBanner');
  const params = new URLSearchParams({
    title: PROBLEM_TITLE,
    topic: PROBLEM_TOPIC,
    difficulty: PROBLEM_DIFFICULTY,
  });
  banner.innerHTML = `
    <div class="solved-banner">
      <div class="msg">✓ Accepted — nice work.</div>
      <a class="btn btn-primary" style="width:auto;" href="${ADD_PROBLEM_URL}?${params.toString()}">Log this to your tracker →</a>
    </div>`;
}

document.getElementById('runBtn')?.addEventListener('click', async () => {
  if (!editor) return;
  setOutputLoading('Running');
  try {
    const res = await fetch(`/api/practice/${PROBLEM_ID}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: editor.getValue(), stdin: SAMPLE_INPUT }),
    });
    const data = await res.json();
    renderRunResult(data);
  } catch (err) {
    renderRunResult({ error: String(err) });
  }
});

document.getElementById('submitBtn')?.addEventListener('click', async () => {
  if (!editor) return;
  setOutputLoading('Judging your submission');
  try {
    const res = await fetch(`/api/practice/${PROBLEM_ID}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: editor.getValue() }),
    });
    const data = await res.json();
    renderSubmitResult(data);
  } catch (err) {
    renderSubmitResult({ error: String(err) });
  }
});
