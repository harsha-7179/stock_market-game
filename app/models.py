from app import db
from datetime import datetime
from flask_login import UserMixin  # ✅ Add this line

class User(db.Model, UserMixin):  # ✅ Inherit UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=100000.0)

    transactions = db.relationship('StockTransaction', backref='user', lazy=True)

class StockTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_name = db.Column(db.String(20), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(4), nullable=False)  # BUY or SELL
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
