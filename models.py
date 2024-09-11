from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    instructions = db.relationship('Instruction', backref='product', lazy=True, cascade='all, delete-orphan')
    price = db.Column(db.Float, nullable=False)
    counselling_histories = db.relationship(
        'CounsellingHistory',
        back_populates='product',
        cascade='all, delete-orphan'
    )


class Instruction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    step = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    pharmacy = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    accumulated_amount = db.Column(db.Float, default=0.0)
    products_cashed_out = db.Column(db.Integer, default=0)
    counselling_fee = db.Column(db.Float, default=0.0)
    products_not_cashed_out = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, full_name, phone, pharmacy, email, password, payment_method, is_admin=False, generate_hash=True):
        self.full_name = full_name
        self.phone = phone
        self.pharmacy = pharmacy
        self.email = email
        self.password = generate_password_hash(password) if generate_hash else password
        self.payment_method = payment_method
        self.is_admin = is_admin

    def check_password(self, password):
        return check_password_hash(self.password, password)


class CounsellingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    counselling_indication = db.Column(db.String(255), nullable=False)
    cashed_out = db.Column(db.Boolean, nullable=False)
    quantity = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product = db.relationship('Product', back_populates='counselling_histories')

    user = db.relationship('User', backref=db.backref('counselling_histories'))

    def __init__(self, product_id, counselling_indication, cashed_out, user_id, quantity):
        self.product_id = product_id
        self.counselling_indication = counselling_indication
        self.cashed_out = cashed_out
        self.user_id = user_id
        self.quantity = quantity
