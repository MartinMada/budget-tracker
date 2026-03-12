from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from database import db
from models import Transaction
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__)

# Halaman daftar transaksi
@transactions_bp.route('/')
def index():
    return render_template('transactions.html')

# API: Ambil semua transaksi
@transactions_bp.route('/api/transactions', methods=['GET'])
def get_transactions():
    month = request.args.get('month')  # format: 2024-01
    
    query = Transaction.query.order_by(Transaction.date.desc())
    
    if month:
        year, mon = month.split('-')
        query = query.filter(
            db.extract('year', Transaction.date) == int(year),
            db.extract('month', Transaction.date) == int(mon)
        )
    
    transactions = query.all()
    return jsonify([t.to_dict() for t in transactions])

# API: Tambah transaksi baru
@transactions_bp.route('/api/transactions', methods=['POST'])
def add_transaction():
    data = request.get_json()
    
    new_transaction = Transaction(
        title    = data['title'],
        amount   = float(data['amount']),
        type     = data['type'],
        category = data['category'],
        date     = datetime.strptime(data['date'], '%Y-%m-%d').date(),
        note     = data.get('note', '')
    )
    
    db.session.add(new_transaction)
    db.session.commit()
    
    return jsonify({'message': 'Transaksi berhasil ditambahkan!', 'data': new_transaction.to_dict()}), 201

# API: Hapus transaksi
@transactions_bp.route('/api/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'Transaksi berhasil dihapus!'})