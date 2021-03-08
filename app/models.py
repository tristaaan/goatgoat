import datetime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def now():
  return datetime.datetime.now()

Base = declarative_base()
Base.query = db.session.query_property()

class User(Base):
  __tablename__ = 'users'

  user_id = db.Column('user_id', db.Integer, primary_key=True)
  email = db.Column('email', db.String(96), unique=True, nullable=False)
  name = db.Column('name', db.String(64), unique=True, nullable=False)
  goatvatar = db.Column('goatvatar', db.Integer, default=1, nullable=False)
  pw = db.Column('password', db.String(128), nullable=False)
  pwResetToken = db.Column('pw_reset_token', db.String, nullable=True)
  pwResetExpires = db.Column('pw_reset_expires', db.DateTime, nullable=True)

  def __init__(self, email, name, password):
    self.email = email
    self.name = name
    self.pw = password


class Goat(Base):
  __tablename__ = 'goats'
  goat_id = db.Column('goat_id', db.Integer, primary_key=True)
  created = db.Column('created', db.DateTime, default=now)
  original_owner_id = db.Column('original_owner_id', db.Integer, db.ForeignKey('users.user_id'), nullable=False)
  owner_id = db.Column('owner_id', db.Integer, db.ForeignKey('users.user_id'), nullable=False)
  owner = relationship(
    User,
    foreign_keys=[owner_id],
    backref=backref('goats',
      uselist=True,
      cascade='delete,all'
    )
  )
  original_owner = relationship(
    User,
    foreign_keys=[original_owner_id]
  )

  def __init__(self, owner):
    self.owner_id = owner
    self.original_owner_id = owner


class Transaction(Base):
  __tablename__ = 'transactions'

  transaction_id = db.Column('transaction_id', db.Integer, primary_key=True)
  goat_id = db.Column('goat_id', db.Integer, db.ForeignKey('goats.goat_id'), nullable=False)
  timestamp = db.Column('timestamp', db.DateTime, default=now)

  from_user_id = db.Column('from_user', db.Integer, db.ForeignKey('users.user_id'), nullable=False)
  from_user = relationship(
    User,
    foreign_keys=[from_user_id]
  )
  to_user_id = db.Column('to_user', db.Integer, db.ForeignKey('users.user_id'), nullable=False)
  to_user = relationship(
    User,
    foreign_keys=[to_user_id]
  )

  def __init__(self, from_user, to_user, goat):
    self.from_user_id = from_user
    self.to_user_id = to_user
    self.goat_id = goat
