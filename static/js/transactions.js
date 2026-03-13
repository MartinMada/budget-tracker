// ── Setup awal ──────────────────────────────────────────────
document.getElementById('date').valueAsDate = new Date();

const now = new Date();
document.getElementById('filterMonth').value =
  `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

loadTransactions();

// ── Load & Render Transaksi ──────────────────────────────────
async function loadTransactions() {
  const month = document.getElementById('filterMonth').value;
  const res   = await fetch(`/api/transactions?month=${month}`);
  const data  = await res.json();
  renderTransactions(data);
}

// Emoji per kategori
const categoryEmoji = {
  'Makan'     : '🍔',
  'Transport' : '🚗',
  'Belanja'   : '🛍️',
  'Hiburan'   : '🎮',
  'Kesehatan' : '💊',
  'Gaji'      : '💰',
  'Lainnya'   : '📦',
};

function formatRupiah(amount) {
  return 'Rp ' + amount.toLocaleString('id-ID');
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
}

function renderTransactions(transactions) {
  const container = document.getElementById('transactionList');
  const countEl   = document.getElementById('txCount');

  if (transactions.length === 0) {
    countEl.textContent = '';
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <p>Belum ada transaksi bulan ini.<br>Tambahkan transaksi pertama Anda!</p>
      </div>`;
    return;
  }

  countEl.textContent = `${transactions.length} transaksi`;

  container.innerHTML = transactions.map((t, i) => `
    <div class="transaction-item" style="animation-delay:${i * 0.04}s">
      <div class="d-flex align-items-center">
        <div class="tx-icon ${t.type}">
          ${categoryEmoji[t.category] || '📦'}
        </div>
        <div>
          <div class="tx-title">${t.title}</div>
          <div class="tx-meta">
            <span class="badge-category">${t.category}</span>
            <span class="tx-date">${formatDate(t.date)}</span>
          </div>
        </div>
      </div>
      <div class="d-flex align-items-center">
        <span class="tx-amount ${t.type}">
          ${t.type === 'income' ? '+' : '−'} ${formatRupiah(t.amount)}
        </span>
        <button class="btn-delete" onclick="deleteTransaction(${t.id})" title="Hapus">
          <i class="bi bi-trash3"></i>
        </button>
      </div>
    </div>
  `).join('');
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

//Tambah Transaksi
async function addTransaction() {
    const title    = document.getElementById('title').value.trim();
    const amount   = document.getElementById('amount').value;
    const type     = document.getElementById('type').value;
    const category = document.getElementById('category').value;
    const date     = document.getElementById('date').value;
    const note     = document.getElementById('note').value.trim();

    if (!title || !amount || !date) {
        showToast('Judul, nominal, dan tanggal wajib diisi!', 'error');
        return;
    }

    const btn = document.querySelector('button[onclick="addTransaction()"]');
    btn.disabled  = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Menyimpan...';

    const res = await fetch('/api/transactions', {
        method : 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken' : getCsrfToken()  // ← tambahan
        },
        body: JSON.stringify({ title, amount, type, category, date, note })
    });

    btn.disabled  = false;
    btn.innerHTML = '<i class="bi bi-plus-lg me-1"></i> Tambah Transaksi';

    if (res.ok) {
        document.getElementById('title').value  = '';
        document.getElementById('amount').value = '';
        document.getElementById('note').value   = '';
        showToast('Transaksi berhasil ditambahkan! ✅', 'success');
        loadTransactions();
    } else {
        const err = await res.json();
        showToast(err.error || 'Gagal menambahkan transaksi.', 'error');
    }
}

//Hapus Transaksi
async function deleteTransaction(id) {
    if (!confirm('Yakin ingin menghapus transaksi ini?')) return;

    const res = await fetch(`/api/transactions/${id}`, {
        method : 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()  // ← tambahan
        }
    });

    if (res.ok) {
        showToast('Transaksi dihapus.', 'success');
        loadTransactions();
    }
}

// Toast Notifikasi
function showToast(message, type = 'success') {
  const existing = document.getElementById('toast-notif');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'toast-notif';
  toast.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    background: ${type === 'success' ? 'rgba(0,212,170,0.15)' : 'rgba(255,92,122,0.15)'};
    border: 1px solid ${type === 'success' ? 'rgba(0,212,170,0.3)' : 'rgba(255,92,122,0.3)'};
    color: ${type === 'success' ? '#00d4aa' : '#ff5c7a'};
    padding: 12px 20px; border-radius: 12px;
    font-size: 14px; font-family: 'DM Sans', sans-serif;
    backdrop-filter: blur(10px);
    animation: fadeUp 0.3s ease;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}