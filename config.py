import os


class Config:
    uri = os.getenv('DATABASE_URL', 'sqlite:///pharmacy.db')

    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'alalani@phldistributions.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'lzcl toul sczv afst')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'alalani@phldistributions.com')
    BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
