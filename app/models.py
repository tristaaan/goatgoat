import datetime
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy

from .enums import TransactionStatus

db = SQLAlchemy()


def now():
  return datetime.datetime.now()

Base = declarative_base()
Base.query = db.session.query_property()

class User(db.Model, Base):
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


class Goat(db.Model, Base):
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


class Transaction(db.Model, Base):
  __tablename__ = 'transactions'

  transaction_id = db.Column('transaction_id', db.Integer, primary_key=True)
  goat_id = db.Column('goat_id', db.Integer, db.ForeignKey('goats.goat_id'), nullable=False)
  timestamp = db.Column('timestamp', db.DateTime, default=now)
  resolved = db.Column('resolved', db.DateTime, nullable=True)
  status = db.Column('status', db.String, nullable=True)
  reason = db.Column('reason', db.String(128), nullable=True)

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

  def __init__(self, from_user, to_user, goat, reason):
    self.from_user_id = from_user
    self.to_user_id = to_user
    self.goat_id = goat
    self.status = TransactionStatus.PENDING.value
    self.reason = reason

  @validates('status')
  def validate_status(self, key, value):
    assert TransactionStatus(value) in {
      TransactionStatus.APPROVED,
      TransactionStatus.DENIED,
      TransactionStatus.PENDING
    }
    return value


class Vote(db.Model, Base):
  __tablename__ = 'votes'

  vote_id = db.Column('vote_id', db.Integer, primary_key=True)
  created = db.Column('created', db.DateTime, default=now)
  voter_id = db.Column('voter_id', db.Integer, db.ForeignKey('users.user_id'))
  voter = relationship(
    User,
    foreign_keys=[voter_id]
  )

  transaction_id = db.Column('transaction_id', db.Integer, db.ForeignKey('transactions.transaction_id'))
  transaction = relationship(
    Transaction,
    foreign_keys=[transaction_id],
    backref=backref('votes',
      uselist=True,
      cascade='delete,all'
    )
  )
  value = db.Column('value', db.Integer, nullable=False) # 0 negative, 1 positive

  def __init__(self, transaction_id, voter_id, value):
    self.transaction_id = transaction_id
    self.voter_id = voter_id
    self.value = value

  @validates('value')
  def validate_value(self, key, value):
    assert value in {-1, 1}
    return value
