from flask import Blueprint, jsonify, request, render_template
from database import db
from models import Transaction

dashboard_bp = Blueprint('dashboard', __name__)

# Halaman dashboard
@dashboard_bp.route('/dashboard')
def dashboard():
    return render_template('index.html')

# API: Data ringkasan untuk dashboard
@dashboard_bp.route('/api/summary', methods=['GET'])
def get_summary():
    month = request.args.get('month')

    query = Transaction.query
    if month:
        year, mon = month.split('-')
        query = query.filter(
            db.extract('year', Transaction.date) == int(year),
            db.extract('month', Transaction.date) == int(mon)
        )

    transactions = query.all()

    total_income  = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')

    # Data per kategori untuk grafik
    categories = {}
    for t in transactions:
        if t.type == 'expense':
            categories[t.category] = categories.get(t.category, 0) + t.amount

    return jsonify({
        'total_income' : total_income,
        'total_expense': total_expense,
        'balance'      : total_income - total_expense,
        'categories'   : categories
    })