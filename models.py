from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    first_name = db.Column(db.String(150), nullable=False) 
    last_name = db.Column(db.String(80), nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False) 
    password = db.Column(db.String(200), nullable=False)


    subjects = db.relationship('Subject', backref='user', lazy='dynamic')

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(50), default='Medium') 

    # dynamic progress tracking
    total_topics = db.Column(db.Integer, default=0)
    completed_topics = db.Column(db.Integer, default=0)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topics = db.relationship('Topic', backref='subject', lazy='dynamic', cascade="all, delete-orphan")

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(50), default='Medium') 
    
    # dynamic progress tracking (on subtopics)
    total_subtopics = db.Column(db.Integer, default=0)
    completed_subtopics = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)

    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    subtopics = db.relationship('Subtopic', backref='topic', lazy='dynamic', cascade="all, delete-orphan")

class Subtopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    date_completed = db.Column(db.DateTime, nullable=True)
    
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)  
    
      