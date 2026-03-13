import os
from flask import Flask
from database import db
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta

# Inisialisasi extension di luar create_app
# agar bisa diimport di file lain
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    # Konfigurasi Dasar
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Secret key — generate otomatis jika tidak ada di environment
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY',
        os.urandom(32).hex()  # Random 32 byte — tidak bisa ditebak
    )

    # Konfigurasi Session
    # Session expired otomatis setelah 2 jam tidak aktif
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    app.config['SESSION_COOKIE_HTTPONLY']    = True   # JS tidak bisa baca cookie
    app.config['SESSION_COOKIE_SAMESITE']    = 'Lax'  # Proteksi CSRF tambahan
    # Aktifkan ini jika sudah pakai HTTPS (production)
    # app.config['SESSION_COOKIE_SECURE'] = True

    # Konfigurasi CSRF
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # Token expired dalam 1 jam

    # Inisialisasi Extension
    db.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)   # Aktifkan CSRF protection untuk semua form

    # Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view    = 'auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu.'

    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.transactions import transactions_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(dashboard_bp)

    # Buat Tabel Database
    with app.app_context():
        db.create_all()
        print("✅ Database siap!")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)  # ← debug=False di production!