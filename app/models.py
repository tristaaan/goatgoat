from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column('user_id', db.Integer, primary_key=True)
    email = db.Column('email', db.String(96), unique=True, nullable=False)
    name = db.Column('name', db.String(64), unique=True, nullable=False)
    pw = db.Column('password', db.String(128), nullable=False)
    pwResetToken = db.Column('pw_reset_token', db.String, nullable=True)
    pwResetExpires = db.Column('pw_reset_expires', db.DateTime, nullable=True)

    def __init__(self, email, name, password):
      self.email = email
      self.name = name
      self.pw = password

    def __repr__(self):
        return '%d' % self.id


class Goat(db.Model):
  __tablename__ = 'goats'
  id = db.Column('goat_id', db.Integer, primary_key=True)
  original_owner = db.Column('original_owner', db.Integer, db.ForeignKey("users.user_id"), nullable=False)
  owner = db.Column('owner', db.Integer, db.ForeignKey("users.user_id"), nullable=False)

  def __init__(self, owner):
      self.owner = owner
      self.original_owner = owner


class Transaction(db.Model):
  __tablename__ = 'transactions'

  id = db.Column(db.Integer, primary_key=True)
  from_user = db.Column('from', db.Integer, db.ForeignKey("users.user_id"), nullable=False)
  to_user = db.Column('to', db.Integer, db.ForeignKey("users.user_id"), nullable=False)
  goat = db.Column('goat_id', db.Integer, db.ForeignKey("goats.goat_id"), nullable=False)
  when = db.Column('timestamp', db.DateTime)

  def __init__(self, from_user, to_user, goat):
    self.from_user = from_user
    self.to_user = to_user
    self.goat = goat

  def __repr__(self):
    return '(%d) %d -> %d' % (goat, from_user, to_user)
