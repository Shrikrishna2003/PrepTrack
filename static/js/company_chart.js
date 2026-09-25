// PrepTrack — company page difficulty chart
if (typeof Chart !== 'undefined') {
  Chart.defaults.color = '#8b909c';
  Chart.defaults.font = { family: "'Inter', sans-serif", size: 11 };
} else {
  console.error('Chart.js failed to load — check static/js/vendor/chart.umd.js is present.');
}

(function renderCompanyDifficultyChart() {
  try {
    const ctx = document.getElementById('companyDifficultyChart');
    if (!ctx || typeof byDifficulty === 'undefined' || typeof Chart === 'undefined') return;

    const order = ['Easy', 'Medium', 'Hard'];
    const colors = { Easy: '#3fcfae', Medium: '#f2a93b', Hard: '#e6667a' };
    const map = {};
    byDifficulty.forEach(d => { map[d.difficulty] = d.c; });
    const labels = order.filter(k => map[k]);
    const values = labels.map(k => map[k]);

    if (!labels.length) {
      ctx.parentElement.innerHTML = '<div class="empty-state" style="padding: 24px 0;">No data yet.</div>';
      return;
    }

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
    console.error('renderCompanyDifficultyChart failed:', err);
  }
})();
