from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from database import db
from models import Transaction
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__)

# Kategori yang diizinkan
VALID_CATEGORIES = ['Makan','Transport','Belanja','Hiburan','Kesehatan','Gaji','Lainnya']
VALID_TYPES      = ['income', 'expense']

def validate_transaction(data):
    """Validasi data transaksi. Return (True, None) atau (False, pesan_error)"""
    if not data.get('title') or not str(data['title']).strip():
        return False, 'Judul wajib diisi.'

    if len(str(data.get('title', ''))) > 100:
        return False, 'Judul maksimal 100 karakter.'

    try:
        amount = float(data.get('amount', 0))
        if amount <= 0:
            return False, 'Nominal harus lebih dari 0.'
        if amount > 999_999_999_999:
            return False, 'Nominal terlalu besar.'
    except (ValueError, TypeError):
        return False, 'Nominal harus berupa angka.'

    if data.get('type') not in VALID_TYPES:
        return False, 'Tipe transaksi tidak valid.'

    if data.get('category') not in VALID_CATEGORIES:
        return False, 'Kategori tidak valid.'

    try:
        datetime.strptime(data.get('date', ''), '%Y-%m-%d')
    except ValueError:
        return False, 'Format tanggal tidak valid.'

    if data.get('note') and len(str(data['note'])) > 200:
        return False, 'Catatan maksimal 200 karakter.'

    return True, None


@transactions_bp.route('/')
@login_required
def index():
    return render_template('transactions.html')


@transactions_bp.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    month = request.args.get('month', '')

    query = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc())

    if month:
        try:
            year, mon = month.split('-')
            # Validasi format bulan
            if not (1 <= int(mon) <= 12) or not (2000 <= int(year) <= 2100):
                return jsonify({'error': 'Format bulan tidak valid.'}), 400
            query = query.filter(
                db.extract('year',  Transaction.date) == int(year),
                db.extract('month', Transaction.date) == int(mon)
            )
        except (ValueError, AttributeError):
            return jsonify({'error': 'Format bulan tidak valid.'}), 400

    return jsonify([t.to_dict() for t in query.all()])


@transactions_bp.route('/api/transactions', methods=['POST'])
@login_required
def add_transaction():
    data = request.get_json(silent=True)  # silent=True agar tidak crash jika bukan JSON

    if not data:
        return jsonify({'error': 'Data tidak valid.'}), 400

    is_valid, error_msg = validate_transaction(data)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    new_t = Transaction(
        title    = str(data['title']).strip(),
        amount   = float(data['amount']),
        type     = data['type'],
        category = data['category'],
        date     = datetime.strptime(data['date'], '%Y-%m-%d').date(),
        note     = str(data.get('note', '')).strip()[:200],
        user_id  = current_user.id
    )

    db.session.add(new_t)
    db.session.commit()
    return jsonify({'message': 'Berhasil!', 'data': new_t.to_dict()}), 201


@transactions_bp.route('/api/transactions/<int:id>', methods=['DELETE'])
@login_required
def delete_transaction(id):
    # filter_by user_id memastikan user hanya bisa hapus miliknya sendiri
    transaction = Transaction.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()

    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'Terhapus!'})