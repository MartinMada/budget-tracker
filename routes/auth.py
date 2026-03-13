from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User

auth_bp = Blueprint('auth', __name__)

#Halaman Register
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email    = request.form.get('email').strip().lower()
        password = request.form.get('password')
        confirm  = request.form.get('confirm_password')

        # Validasi input
        if not username or not email or not password:
            flash('Semua field wajib diisi!', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash('Password dan konfirmasi password tidak cocok!', 'error')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password minimal 6 karakter!', 'error')
            return redirect(url_for('auth.register'))

        # Cek apakah username atau email sudah dipakai
        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan, coba yang lain.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar.', 'error')
            return redirect(url_for('auth.register'))

        # Hash password sebelum disimpan
        # JANGAN PERNAH simpan password as plain text!
        hashed_password = generate_password_hash(password)

        # Simpan user baru ke database
        new_user = User(
            username = username,
            email    = email,
            password = hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


#Halaman Login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login_input').strip()
        password    = request.form.get('password')
        remember    = request.form.get('remember') == 'on'

        # Cari user berdasarkan username atau email
        user = User.query.filter(
            (User.username == login_input) |
            (User.email == login_input.lower())
        ).first()

        # Verifikasi user dan password
        if not user or not check_password_hash(user.password, password):
            flash('Username/email atau password salah.', 'error')
            return redirect(url_for('auth.login'))

        # Login berhasil — buat session
        # remember=True = session bertahan meski browser ditutup
        login_user(user, remember=remember)

        # Redirect ke halaman yang ingin dikunjungi sebelumnya
        # atau ke dashboard jika tidak ada
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.dashboard'))

    return render_template('auth/login.html')


#Logout
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda berhasil logout.', 'success')
    return redirect(url_for('auth.login'))