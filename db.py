# db.py
from flask_sqlalchemy import SQLAlchemy

# create the SQLAlchemy “db” object, but don’t bind it to an blueprints yet
db = SQLAlchemy()
