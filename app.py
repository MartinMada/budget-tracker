from flask import Flask
from database import db
from models import Transaction

def create_app():
    app = Flask(__name__)

    # Konfigurasi database — simpan di file lokal bernama budget.db
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'budget-tracker-secret-123'

    # Hubungkan database ke aplikasi
    db.init_app(app)

    # Import dan daftarkan routes
    from routes.transactions import transactions_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(transactions_bp)
    app.register_blueprint(dashboard_bp)

    # Buat semua tabel jika belum ada
    with app.app_context():
        db.create_all()
        print("✅ Database siap!")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)