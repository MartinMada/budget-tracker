from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import db
from models import Category

categories_bp = Blueprint('categories', __name__)

# Kategori default (selalu tersedia untuk semua user)
DEFAULT_CATEGORIES = {
    'expense': ['Makan', 'Transport', 'Belanja', 'Hiburan', 'Kesehatan', 'Lainnya'],
    'income' : ['Gaji', 'Freelance', 'Investasi', 'Lainnya']
}

# ── Ambil semua kategori (default + custom) ──────────────────
@categories_bp.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    cat_type = request.args.get('type')  # 'income' atau 'expense'

    # Ambil kategori custom milik user
    query = Category.query.filter_by(user_id=current_user.id)
    if cat_type:
        query = query.filter_by(type=cat_type)
    custom = query.order_by(Category.name).all()

    # Gabungkan default + custom
    result = {}
    for t in ['income', 'expense']:
        if cat_type and cat_type != t:
            continue
        defaults = [{'id': None, 'name': c, 'type': t, 'is_default': True}
                    for c in DEFAULT_CATEGORIES[t]]
        customs  = [{'id': c.id, 'name': c.name, 'type': c.type, 'is_default': False}
                    for c in custom if c.type == t]
        result[t] = defaults + customs

    return jsonify(result)


# ── Tambah kategori custom ───────────────────────────────────
@categories_bp.route('/api/categories', methods=['POST'])
@login_required
def add_category():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Data tidak valid.'}), 400

    name     = str(data.get('name', '')).strip()
    cat_type = data.get('type', '')

    if not name:
        return jsonify({'error': 'Nama kategori wajib diisi.'}), 400

    if len(name) > 50:
        return jsonify({'error': 'Nama kategori maksimal 50 karakter.'}), 400

    if cat_type not in ['income', 'expense']:
        return jsonify({'error': 'Tipe harus income atau expense.'}), 400

    # Cek duplikat dengan kategori default
    all_defaults = DEFAULT_CATEGORIES['income'] + DEFAULT_CATEGORIES['expense']
    if name in all_defaults:
        return jsonify({'error': 'Nama kategori sudah ada di daftar default.'}), 400

    # Cek duplikat dengan kategori custom user
    existing = Category.query.filter_by(
        user_id=current_user.id,
        name=name,
        type=cat_type
    ).first()
    if existing:
        return jsonify({'error': 'Kategori ini sudah ada.'}), 400

    # Batasi maksimal 20 kategori custom per user
    total = Category.query.filter_by(user_id=current_user.id).count()
    if total >= 20:
        return jsonify({'error': 'Maksimal 20 kategori custom per akun.'}), 400

    new_cat = Category(
        name    = name,
        type    = cat_type,
        user_id = current_user.id
    )
    db.session.add(new_cat)
    db.session.commit()

    return jsonify({'message': 'Kategori berhasil ditambahkan!',
                    'data': new_cat.to_dict()}), 201


# ── Hapus kategori custom ────────────────────────────────────
@categories_bp.route('/api/categories/<int:id>', methods=['DELETE'])
@login_required
def delete_category(id):
    cat = Category.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()

    db.session.delete(cat)
    db.session.commit()
    return jsonify({'message': 'Kategori dihapus.'})