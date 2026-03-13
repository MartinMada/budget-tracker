from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User
from extensions import limiter # ← Import limiter dari extensions.py
import re

auth_bp = Blueprint('auth', __name__)

# Helper: Validasi Kekuatan Password
def validate_password(password):
    """
    Kembalikan list error. Jika list kosong = password valid.
    """
    errors = []
    if len(password) < 8:
        errors.append('Minimal 8 karakter.')
    if not re.search(r'[A-Z]', password):
        errors.append('Minimal 1 huruf kapital.')
    if not re.search(r'[0-9]', password):
        errors.append('Minimal 1 angka.')
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append('Minimal 1 karakter spesial (!@#$%^&*).')

    # Cek password umum yang mudah ditebak
    common = ['password', '12345678', 'qwerty123', 'iloveyou']
    if password.lower() in common:
        errors.append('Password terlalu umum, gunakan yang lebih unik.')

    return errors

# Register
@auth_bp.route('/register', methods=['GET', 'POST'])
# Batasi: maksimal 5 kali register per jam dari IP yang sama
@limiter.limit("5 per hour")
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # ── Validasi Field Kosong ──
        if not username or not email or not password:
            flash('Semua field wajib diisi!', 'error')
            return redirect(url_for('auth.register'))

        # ── Validasi Format Username ──
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
            flash('Username hanya boleh huruf, angka, underscore. (3-30 karakter)', 'error')
            return redirect(url_for('auth.register'))

        # ── Validasi Format Email ──
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash('Format email tidak valid.', 'error')
            return redirect(url_for('auth.register'))

        # ── Validasi Password ──
        pw_errors = validate_password(password)
        if pw_errors:
            for err in pw_errors:
                flash(err, 'error')
            return redirect(url_for('auth.register'))

        # ── Validasi Konfirmasi Password ──
        if password != confirm:
            flash('Password dan konfirmasi tidak cocok!', 'error')
            return redirect(url_for('auth.register'))

        # ── Cek Duplikat (Pesan GENERIK — cegah enumeration) ──
        # Jangan beritahu mana yang sudah ada!
        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            flash('Username atau email sudah digunakan.', 'error')
            return redirect(url_for('auth.register'))

        # ── Simpan User Baru ──
        new_user = User(
            username = username,
            email    = email,
            password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# Login
@auth_bp.route('/login', methods=['GET', 'POST'])
# Batasi: maksimal 10 percobaan login per menit dari IP yang sama
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password    = request.form.get('password', '')
        remember    = request.form.get('remember') == 'on'

        # Validasi tidak kosong
        if not login_input or not password:
            flash('Username/email dan password wajib diisi.', 'error')
            return redirect(url_for('auth.login'))

        # Cari user
        user = User.query.filter(
            (User.username == login_input) |
            (User.email == login_input.lower())
        ).first()

        # ── Pesan Error GENERIK — cegah enumeration ──
        # Jangan beritahu apakah username/email-nya yang salah!
        if not user or not check_password_hash(user.password, password):
            flash('Username/email atau password salah.', 'error')
            return redirect(url_for('auth.login'))

        # ── Login Berhasil ──
        login_user(user, remember=remember)

        # Aktifkan permanent session agar timeout berjalan
        session.permanent = True

        next_page = request.args.get('next')

        # Validasi next_page — pastikan tidak redirect ke URL eksternal
        # (Open Redirect vulnerability)
        if next_page and not next_page.startswith('/'):
            next_page = None

        return redirect(next_page or url_for('dashboard.dashboard'))

    return render_template('auth/login.html')


# Logout
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    # Hapus seluruh session data
    session.clear()
    flash('Anda berhasil logout.', 'success')
    return redirect(url_for('auth.login'))


# ── Halaman Profil ────────────────────────────────────────────
@auth_bp.route('/profile')
@login_required
def profile():
    # Hitung total transaksi user
    from models import Transaction
    total_tx = Transaction.query.filter_by(user_id=current_user.id).count()
    return render_template('profile.html', total_tx=total_tx)


# ── Update Username & Email ───────────────────────────────────
@auth_bp.route('/profile/update-info', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def update_info():
    username = request.form.get('username', '').strip()
    email    = request.form.get('email', '').strip().lower()

    # Validasi tidak kosong
    if not username or not email:
        flash('Username dan email wajib diisi.', 'error')
        return redirect(url_for('auth.profile'))

    # Validasi format username
    if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
        flash('Username hanya boleh huruf, angka, underscore (3-30 karakter).', 'error')
        return redirect(url_for('auth.profile'))

    # Validasi format email
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        flash('Format email tidak valid.', 'error')
        return redirect(url_for('auth.profile'))

    # Cek duplikat — kecuali milik user sendiri
    existing_username = User.query.filter(
        User.username == username,
        User.id != current_user.id
    ).first()
    if existing_username:
        flash('Username sudah digunakan orang lain.', 'error')
        return redirect(url_for('auth.profile'))

    existing_email = User.query.filter(
        User.email == email,
        User.id != current_user.id
    ).first()
    if existing_email:
        flash('Email sudah digunakan orang lain.', 'error')
        return redirect(url_for('auth.profile'))

    # Simpan perubahan
    current_user.username = username
    current_user.email    = email
    db.session.commit()

    flash('Profil berhasil diupdate!', 'success')
    return redirect(url_for('auth.profile'))


# ── Update Password ───────────────────────────────────────────
@auth_bp.route('/profile/update-password', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def update_password():
    current_pw  = request.form.get('current_password', '')
    new_pw      = request.form.get('new_password', '')
    confirm_pw  = request.form.get('confirm_password', '')

    # Verifikasi password lama
    if not check_password_hash(current_user.password, current_pw):
        flash('Password saat ini tidak sesuai.', 'error')
        return redirect(url_for('auth.profile'))

    # Validasi password baru
    pw_errors = validate_password(new_pw)
    if pw_errors:
        for err in pw_errors:
            flash(err, 'error')
        return redirect(url_for('auth.profile'))

    # Cek konfirmasi
    if new_pw != confirm_pw:
        flash('Password baru dan konfirmasi tidak cocok.', 'error')
        return redirect(url_for('auth.profile'))

    # Pastikan password baru berbeda dari yang lama
    if check_password_hash(current_user.password, new_pw):
        flash('Password baru tidak boleh sama dengan password lama.', 'error')
        return redirect(url_for('auth.profile'))

    # Simpan password baru
    current_user.password = generate_password_hash(
        new_pw, method='pbkdf2:sha256', salt_length=16
    )
    db.session.commit()

    flash('Password berhasil diubah!', 'success')
    return redirect(url_for('auth.profile'))


# Handler Error Rate Limit
from flask_limiter.errors import RateLimitExceeded

@auth_bp.errorhandler(RateLimitExceeded)
def handle_rate_limit(e):
    flash('Terlalu banyak percobaan. Silakan tunggu beberapa saat.', 'error')
    return redirect(url_for('auth.login')), 429