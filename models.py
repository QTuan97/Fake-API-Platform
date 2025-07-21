from datetime import datetime
from db import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow,
                             onupdate=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    owner_user = db.Column(db.Integer, nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow,
                             onupdate=datetime.utcnow, nullable=False)
    collections = db.relationship('Collection', backref='project', cascade='all, delete-orphan')
    mock_rules = db.relationship('MockRule', backref='project', cascade='all, delete-orphan')

class Collection(db.Model):
    __tablename__ = 'collections'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow,
                             onupdate=datetime.utcnow, nullable=False)
    requests = db.relationship('Request', backref='collection', cascade='all, delete-orphan')

class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(
        db.Integer,
        db.ForeignKey('collections.id', ondelete='CASCADE'),
        nullable=False
    )
    name = db.Column(db.Text, nullable=False)
    method = db.Column(db.String(10), nullable=False)
    path = db.Column(db.Text, nullable=False)
    headers = db.Column(db.JSON, default={}, nullable=False)
    query_params = db.Column(db.JSON, default={}, nullable=False)
    body_template = db.Column(db.Text, nullable=True)
    # body_template = db.Column(db.JSON, nullable=True)
    tests = db.Column(
        db.JSON,
        default=lambda: {'responseType': 'JSON', 'status': 200, 'delay_ms': 0},
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

class MockRule(db.Model):
    __tablename__ = 'mock_rules'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    match_criteria = db.Column(db.JSON, nullable=False)
    response_sequence = db.Column(db.JSON, nullable=False,
                                  default=list)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)