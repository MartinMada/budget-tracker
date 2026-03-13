from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from database import db
from models import Transaction
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/')
@login_required  # ← Proteksi: wajib login
def index():
    return render_template('transactions.html')

@transactions_bp.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    month = request.args.get('month')

    # Filter HANYA transaksi milik user yang sedang login
    query = Transaction.query.filter_by(
        user_id=current_user.id  # ← Kunci isolasi data
    ).order_by(Transaction.date.desc())

    if month:
        year, mon = month.split('-')
        query = query.filter(
            db.extract('year', Transaction.date) == int(year),
            db.extract('month', Transaction.date) == int(mon)
        )

    transactions = query.all()
    return jsonify([t.to_dict() for t in transactions])

@transactions_bp.route('/api/transactions', methods=['POST'])
@login_required
def add_transaction():
    data = request.get_json()

    new_transaction = Transaction(
        title    = data['title'],
        amount   = float(data['amount']),
        type     = data['type'],
        category = data['category'],
        date     = datetime.strptime(data['date'], '%Y-%m-%d').date(),
        note     = data.get('note', ''),
        user_id  = current_user.id  # ← Tandai transaksi milik siapa
    )

    db.session.add(new_transaction)
    db.session.commit()
    return jsonify({'message': 'Berhasil!', 'data': new_transaction.to_dict()}), 201

@transactions_bp.route('/api/transactions/<int:id>', methods=['DELETE'])
@login_required
def delete_transaction(id):
    # Pastikan transaksi milik user yang login, bukan user lain!
    transaction = Transaction.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'Terhapus!'})