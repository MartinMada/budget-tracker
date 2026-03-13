from database import db
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(50), unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password     = db.Column(db.String(200), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('Transaction', backref='user',
                                   lazy=True, cascade='all, delete')
    categories   = db.relationship('Category', backref='user',
                                   lazy=True, cascade='all, delete')

    def __repr__(self):
        return f'<User {self.username}>'


# Kategori Custom
class Category(db.Model):
    __tablename__ = 'categories'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(50), nullable=False)
    type       = db.Column(db.String(10), nullable=False)  # 'income' atau 'expense'
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id'  : self.id,
            'name': self.name,
            'type': self.type
        }


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