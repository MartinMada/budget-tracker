import os
from flask import Flask
from database import db
from flask_login import LoginManager
from extensions import limiter, csrf  # ← Import dari extensions.py
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect, validate_csrf
from flask import request as flask_request

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key-ganti-di-production')

    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    app.config['SESSION_COOKIE_HTTPONLY']    = True
    app.config['SESSION_COOKIE_SAMESITE']    = 'Lax'
    app.config['WTF_CSRF_TIME_LIMIT']        = 3600

    db.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    @app.before_request
    def check_csrf():
        # Endpoint API yang dipanggil JS menggunakan header X-CSRFToken
        # Flask-WTF otomatis validasi dari header ini
        pass

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view    = 'auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu.'

    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.transactions import transactions_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        db.create_all()
        print("✅ Database siap!")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)