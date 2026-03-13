from database import db
from datetime import datetime
from flask_login import UserMixin

# UserMixin menambahkan method wajib flask-login:
# is_authenticated, is_active, is_anonymous, get_id
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(50), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi: satu user punya banyak transaksi
    # cascade='all, delete' = jika user dihapus, semua transaksinya ikut terhapus
    transactions = db.relationship('Transaction', backref='user',
                                   lazy=True, cascade='all, delete')

    def __repr__(self):
        return f'<User {self.username}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(100), nullable=False)
    amount     = db.Column(db.Float, nullable=False)
    type       = db.Column(db.String(10), nullable=False)
    category   = db.Column(db.String(50), nullable=False)
    date       = db.Column(db.Date, nullable=False)
    note       = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key — setiap transaksi dimiliki oleh satu user
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id'      : self.id,
            'title'   : self.title,
            'amount'  : self.amount,
            'type'    : self.type,
            'category': self.category,
            'date'    : self.date.strftime('%Y-%m-%d'),
            'note'    : self.note
        }