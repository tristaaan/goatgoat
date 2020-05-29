from flask import Blueprint, render_template
from sqlalchemy.sql import select, func

views = Blueprint('views', __name__,
                        template_folder='templates')

@views.route('/')
def index():
    return render_template("home.html")

# AUTH
@views.route("/login")
def login():
  return render_template("login.html")

@views.route("/sign-up")
def sign_up():
  return render_template("sign-up.html")

@views.route("/reset")
def reset():
  return render_template("reset.html")

@views.route("/forgot")
def forgot():
  return render_template("forgot.html")

# USER
@views.route("/user/<username>")
def userpage(username):
  return render_template("user.html")
