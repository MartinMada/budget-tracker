import os
from flask import Flask
from database import db
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Inisialisasi database
    db.init_app(app)

    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    # Jika user belum login dan coba akses halaman protected,
    # redirect ke halaman login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu.'

    # Flask-Login butuh tahu cara load user dari database
    # berdasarkan ID yang disimpan di session
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Daftarkan semua blueprint (routes)
    from routes.auth import auth_bp
    from routes.transactions import transactions_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(dashboard_bp)

    # Buat semua tabel
    with app.app_context():
        db.create_all()
        print("✅ Database siap!")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)