// ── Setup awal ──────────────────────────────────────────────
let incomeExpenseChart = null;
let categoryChart      = null;

const now = new Date();
document.getElementById('filterMonth').value =
  `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

loadDashboard();

// ── Load Data Dashboard ──────────────────────────────────────
async function loadDashboard() {
  const month = document.getElementById('filterMonth').value;
  const res   = await fetch(`/api/summary?month=${month}`);
  const data  = await res.json();
  updateSummaryCards(data);
  renderCharts(data);
}

function formatRupiah(amount) {
  return 'Rp ' + Math.abs(amount).toLocaleString('id-ID');
}

// ── Update Kartu Ringkasan ───────────────────────────────────
function updateSummaryCards(data) {
  document.getElementById('totalIncome').textContent  = formatRupiah(data.total_income);
  document.getElementById('totalExpense').textContent = formatRupiah(data.total_expense);

  const balanceEl = document.getElementById('balance');
  balanceEl.textContent = formatRupiah(data.balance);
  balanceEl.className   = 'summary-value ' + (
    data.balance > 0 ? 'positive' :
    data.balance < 0 ? 'negative' : 'neutral'
  );
}

// ── Render Charts ────────────────────────────────────────────
Chart.defaults.color          = '#6b6b80';
Chart.defaults.borderColor    = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family    = "'DM Sans', sans-serif";

function renderCharts(data) {
  if (incomeExpenseChart) incomeExpenseChart.destroy();
  if (categoryChart)      categoryChart.destroy();

  // ── Chart 1: Bar — Pemasukan vs Pengeluaran ──
  incomeExpenseChart = new Chart(
    document.getElementById('incomeExpenseChart'), {
    type: 'bar',
    data: {
      labels: ['Pemasukan', 'Pengeluaran'],
      datasets: [{
        data: [data.total_income, data.total_expense],
        backgroundColor: [
          'rgba(0,212,170,0.2)',
          'rgba(255,92,122,0.2)'
        ],
        borderColor: ['#00d4aa', '#ff5c7a'],
        borderWidth: 2,
        borderRadius: 10,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(17,17,24,0.95)',
          borderColor    : 'rgba(255,255,255,0.08)',
          borderWidth    : 1,
          padding        : 12,
          callbacks: {
            label: ctx => ' Rp ' + ctx.raw.toLocaleString('id-ID')
          }
        }
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          beginAtZero: true,
          ticks: {
            callback: val => 'Rp ' + (val / 1000) + 'k'
          }
        }
      }
    }
  });

  // ── Chart 2: Doughnut — Per Kategori ──
  const categories = Object.keys(data.categories);
  const amounts    = Object.values(data.categories);

  if (categories.length === 0) {
    // Tampilkan placeholder jika tidak ada data
    categoryChart = new Chart(
      document.getElementById('categoryChart'), {
      type: 'doughnut',
      data: {
        labels  : ['Belum ada data'],
        datasets: [{ data: [1], backgroundColor: ['rgba(255,255,255,0.05)'], borderWidth: 0 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        cutout: '70%'
      }
    });
    return;
  }

  const palette = [
    '#7b61ff','#00d4aa','#ff5c7a',
    '#f59e0b','#3b82f6','#ec4899','#10b981'
  ];

  categoryChart = new Chart(
    document.getElementById('categoryChart'), {
    type: 'doughnut',
    data: {
      labels  : categories,
      datasets: [{
        data           : amounts,
        backgroundColor: palette.slice(0, categories.length),
        borderColor    : '#111118',
        borderWidth    : 3,
        hoverOffset    : 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position : 'bottom',
          labels   : {
            padding    : 16,
            usePointStyle: true,
            pointStyle : 'circle',
            font       : { size: 12 }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17,17,24,0.95)',
          borderColor    : 'rgba(255,255,255,0.08)',
          borderWidth    : 1,
          padding        : 12,
          callbacks: {
            label: ctx => ` Rp ${ctx.raw.toLocaleString('id-ID')}`
          }
        }
      }
    }
  });
}