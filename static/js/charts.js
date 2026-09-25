// PrepTrack — dashboard charts + streak heatmap
// Expects heatmapData, last30, byDifficulty, byCompany to be defined inline before this file loads.

(function renderHeatmap() {
  const el = document.getElementById('heatmap');
  if (!el || typeof heatmapData === 'undefined') return;

  const max = Math.max(1, ...heatmapData.map(d => d.count));
  heatmapData.forEach(d => {
    const cell = document.createElement('div');
    cell.className = 'cell';
    let level = 0;
    if (d.count > 0) {
      const ratio = d.count / max;
      level = ratio > 0.66 ? 3 : ratio > 0.33 ? 2 : 1;
    }
    cell.dataset.level = level;
    cell.title = `${d.date} — ${d.count} solved`;
    el.appendChild(cell);
  });
})();

if (typeof Chart === 'undefined') {
  console.error('Chart.js failed to load — charts will stay blank. Check static/js/vendor/chart.umd.js is present and static files are being served.');
} else {
  Chart.defaults.color = '#8b909c';
  Chart.defaults.font = { family: "'Inter', sans-serif", size: 11 };
  Chart.defaults.borderColor = '#1b1f27';
}

(function renderTrendChart() {
  try {
    const ctx = document.getElementById('trendChart');
    if (!ctx || typeof last30 === 'undefined' || typeof Chart === 'undefined') return;

    const labels = last30.map(d => d.solved_date.slice(5));
    const values = last30.map(d => d.c);

    new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          data: values,
          borderColor: '#f2a93b',
          backgroundColor: 'rgba(242,169,59,0.12)',
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
          y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#1b1f27' } },
        },
        maintainAspectRatio: false,
      },
    });
  } catch (err) {
    console.error('renderTrendChart failed:', err);
  }
})();

(function renderDifficultyChart() {
  try {
    const ctx = document.getElementById('difficultyChart');
    if (!ctx || typeof byDifficulty === 'undefined' || typeof Chart === 'undefined') return;

    const order = ['Easy', 'Medium', 'Hard'];
    const colors = { Easy: '#3fcfae', Medium: '#f2a93b', Hard: '#e6667a' };
    const map = {};
    byDifficulty.forEach(d => { map[d.difficulty] = d.c; });
    const labels = order.filter(k => map[k]);
    const values = labels.map(k => map[k]);

    if (!labels.length) return;

    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: labels.map(l => colors[l]),
          borderColor: '#14171d',
          borderWidth: 3,
        }],
      },
      options: {
        cutout: '68%',
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 14 } } },
        maintainAspectRatio: false,
      },
    });
  } catch (err) {
    console.error('renderDifficultyChart failed:', err);
  }
})();

(function renderCompanyChart() {
  try {
    const ctx = document.getElementById('companyChart');
    if (!ctx || typeof byCompany === 'undefined' || typeof Chart === 'undefined') return;

    const labels = byCompany.map(d => d.company);
    const values = byCompany.map(d => d.c);

    new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: '#3fcfae',
          borderRadius: 3,
          maxBarThickness: 34,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#1b1f27' } },
        },
        maintainAspectRatio: false,
      },
    });
  } catch (err) {
    console.error('renderCompanyChart failed:', err);
  }
})();
