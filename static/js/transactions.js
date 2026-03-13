// ── Setup Awal ───────────────────────────────────────────────
document.getElementById('date').valueAsDate = new Date();

const now = new Date();
document.getElementById('filterMonth').value =
  `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

loadCategories().then(() => loadTransactions());

document.getElementById('type').addEventListener('change', loadCategories);

async function loadCategories() {
  const type = document.getElementById('type').value;
  const res  = await fetch(`/api/categories?type=${type}`);
  const data = await res.json();

  const select   = document.getElementById('category');
  const current  = select.value;
  const cats     = data[type] || [];

  select.innerHTML = cats.map(c => `
    <option value="${c.name}" ${c.name === current ? 'selected' : ''}>
      ${c.is_default ? getCategoryEmoji(c.name) : '⭐'} ${c.name}
      ${!c.is_default ? '(custom)' : ''}
    </option>
  `).join('');
}

function getCategoryEmoji(name) {
  const map = {
    'Makan':'🍔','Transport':'🚗','Belanja':'🛍️','Hiburan':'🎮',
    'Kesehatan':'💊','Gaji':'💰','Freelance':'💻','Investasi':'📈',
    'Lainnya':'📦'
  };
  return map[name] || '📦';
}

// ── CSRF Token ───────────────────────────────────────────────
function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// ── Format Helpers ───────────────────────────────────────────
const categoryEmoji = {
  'Makan': '🍔', 'Transport': '🚗', 'Belanja': '🛍️',
  'Hiburan': '🎮', 'Kesehatan': '💊', 'Gaji': '💰', 'Lainnya': '📦'
};

function formatRupiah(amount) {
  return 'Rp ' + amount.toLocaleString('id-ID');
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('id-ID', {
    day: 'numeric', month: 'short', year: 'numeric'
  });
}

// ── Load & Render Transaksi ──────────────────────────────────
async function loadTransactions() {
  const month = document.getElementById('filterMonth').value;
  const res   = await fetch(`/api/transactions?month=${month}`);
  const data  = await res.json();
  renderTransactions(data);
}

function renderTransactions(transactions) {
  const container = document.getElementById('transactionList');
  const countEl   = document.getElementById('txCount');

  if (transactions.length === 0) {
    countEl.textContent = '';
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <p>Belum ada transaksi bulan ini.<br>
           Tambahkan transaksi pertama Anda!</p>
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
      <div class="d-flex align-items-center gap-1">
        <span class="tx-amount ${t.type}">
          ${t.type === 'income' ? '+' : '−'} ${formatRupiah(t.amount)}
        </span>
        <!-- Tombol Edit -->
        <button class="btn-delete" onclick="startEdit(${JSON.stringify(t).replace(/"/g, '&quot;')})"
                title="Edit" style="color:var(--accent)">
          <i class="bi bi-pencil"></i>
        </button>
        <!-- Tombol Hapus -->
        <button class="btn-delete" onclick="deleteTransaction(${t.id})"
                title="Hapus">
          <i class="bi bi-trash3"></i>
        </button>
      </div>
    </div>
  `).join('');
}

// ── Mode Edit — Isi Form dengan Data Lama ────────────────────
function startEdit(transaction) {
  // Isi form dengan data transaksi yang dipilih
  document.getElementById('editId').value    = transaction.id;
  document.getElementById('title').value     = transaction.title;
  document.getElementById('amount').value    = transaction.amount;
  document.getElementById('type').value      = transaction.type;
  document.getElementById('category').value  = transaction.category;
  document.getElementById('date').value      = transaction.date;
  document.getElementById('note').value      = transaction.note || '';

  // Ubah tampilan form ke mode edit
  document.getElementById('formTitle').textContent = 'Edit Transaksi';
  document.getElementById('formIcon').innerHTML    = '<i class="bi bi-pencil"></i>';
  document.getElementById('formIcon').style.background = 'rgba(245,158,11,0.15)';
  document.getElementById('formIcon').style.color       = '#f59e0b';
  document.getElementById('submitBtn').innerHTML =
    '<i class="bi bi-check-lg me-1"></i> Simpan Perubahan';
  document.getElementById('submitBtn').style.background =
    'linear-gradient(135deg, #f59e0b, #fbbf24)';
  document.getElementById('cancelBtn').style.display = 'block';

  // Scroll ke form agar terlihat (penting di mobile)
  document.querySelector('.card').scrollIntoView({ behavior: 'smooth' });
}

// ── Batal Edit — Kembalikan Form ke Mode Tambah ──────────────
function cancelEdit() {
  document.getElementById('editId').value   = '';
  document.getElementById('title').value    = '';
  document.getElementById('amount').value   = '';
  document.getElementById('note').value     = '';
  document.getElementById('date').valueAsDate = new Date();

  // Kembalikan tampilan form ke mode tambah
  document.getElementById('formTitle').textContent = 'Tambah Transaksi';
  document.getElementById('formIcon').innerHTML    = '<i class="bi bi-plus-lg"></i>';
  document.getElementById('formIcon').style.background = 'rgba(123,97,255,0.15)';
  document.getElementById('formIcon').style.color       = 'var(--accent)';
  document.getElementById('submitBtn').innerHTML =
    '<i class="bi bi-plus-lg me-1"></i> Tambah Transaksi';
  document.getElementById('submitBtn').style.background = '';
  document.getElementById('cancelBtn').style.display = 'none';
}

// ── Submit Form — Tambah atau Edit ───────────────────────────
async function submitForm() {
  const editId   = document.getElementById('editId').value;
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

  const btn = document.getElementById('submitBtn');
  const originalHTML  = btn.innerHTML;
  btn.disabled  = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Menyimpan...';

  // Tentukan URL dan method berdasarkan mode
  const url    = editId ? `/api/transactions/${editId}` : '/api/transactions';
  const method = editId ? 'PUT' : 'POST';

  const res = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken' : getCsrfToken()
    },
    body: JSON.stringify({ title, amount, type, category, date, note })
  });

  btn.disabled  = false;
  btn.innerHTML = originalHTML;

  if (res.ok) {
    cancelEdit();  // Reset form ke mode tambah
    showToast(
      editId ? 'Transaksi berhasil diupdate! ✅' : 'Transaksi berhasil ditambahkan! ✅',
      'success'
    );
    loadTransactions();
  } else {
    const err = await res.json();
    showToast(err.error || 'Gagal menyimpan transaksi.', 'error');
  }
}

// ── Hapus Transaksi ──────────────────────────────────────────
async function deleteTransaction(id) {
  if (!confirm('Yakin ingin menghapus transaksi ini?')) return;

  const res = await fetch(`/api/transactions/${id}`, {
    method : 'DELETE',
    headers: { 'X-CSRFToken': getCsrfToken() }
  });

  if (res.ok) {
    showToast('Transaksi dihapus.', 'success');
    loadTransactions();
  }
}

// ── Toast Notifikasi ─────────────────────────────────────────
function showToast(message, type = 'success') {
  const existing = document.getElementById('toast-notif');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'toast-notif';
  toast.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    background: ${type === 'success'
      ? 'rgba(0,212,170,0.15)' : 'rgba(255,92,122,0.15)'};
    border: 1px solid ${type === 'success'
      ? 'rgba(0,212,170,0.3)' : 'rgba(255,92,122,0.3)'};
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

// ── Export PDF ───────────────────────────────────────────────
function exportPDF() {
  const month = document.getElementById('filterMonth').value;
  const url   = `/api/export/pdf${month ? '?month=' + month : ''}`;

  // Buka di tab baru → browser otomatis download
  window.open(url, '_blank');
}