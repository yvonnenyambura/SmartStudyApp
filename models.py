from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    first_name = db.Column(db.String(150), nullable=False) 
    last_name = db.Column(db.String(80), nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False) 
    password = db.Column(db.String(200), nullable=False)