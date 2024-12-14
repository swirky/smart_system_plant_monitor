import os

import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres:Mar123321@127.0.0.1/monitor_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'unique-secret-key')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'plantmonitor.w66020@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'tdwt qjif twik aexe')
    MAIL_DEFAULT_SENDER = 'marek.koksu17@gmail.com'