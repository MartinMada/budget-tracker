from database import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id       = db.Column(db.Integer, primary_key=True)
    title    = db.Column(db.String(100), nullable=False)
    amount   = db.Column(db.Float, nullable=False)
    type     = db.Column(db.String(10), nullable=False)  # 'income' atau 'expense'
    category = db.Column(db.String(50), nullable=False)
    date     = db.Column(db.Date, nullable=False)
    note     = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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