from flask import Blueprint, render_template, request, redirect, current_app
from flask_graphql_auth import get_jwt_data
from sqlalchemy.sql import select, func

views = Blueprint('views', __name__, template_folder='templates')


def get_credentials():
  token = request.cookies.get('token', None)
  if token is not None and len(token):
    return get_jwt_data(token, 'access')
  return None


def redirect_else_render(page):
  data = get_credentials()
  # skip page and redirect to user's page
  if data is not None:
    username = data['identity']
    return redirect(f'/{username}', code=302)
  return render_template(page, logged_in=False)


@views.route('/')
def index():
  data = get_credentials()
  if data is not None:
    username = data['identity']
    return redirect(f'/{username}', code=302)
  return render_template('home.html', logged_in=(get_credentials() is not None))


# AUTH
@views.route('/login', methods=['GET'])
def login():
  return redirect_else_render('login.html')


@views.route('/sign-up')
def sign_up():
  return redirect_else_render('sign-up.html')


@views.route('/reset')
def reset():
  return render_template('reset.html')


@views.route('/forgot')
def forgot():
  return render_template('forgot.html')


# USER
@views.route('/settings', methods=['GET'])
def user_settings():
  token = request.cookies.get('token', None)
  if token is not None:
    data = get_jwt_data(token, 'access')
    username = data['identity']
    return render_template('settings.html',
      goat_imgs=current_app.config['goat_imgs'],
      username=username,
      logged_in=True
    )

  return redirect(f'/', code=302)


@views.route('/<username>', methods=['GET'])
def userpage(username):
  token = request.cookies.get('token', None)

  if token is not None:
    data = get_jwt_data(token, 'access')
    token_username = data['identity']
    # if visiting your own page render 'my page'
    if token_username == username:
      return render_template(
        'my-userpage.html',
        username=username,
        logged_in=True,
        goat_imgs=current_app.config['goat_imgs']
      )

    # else render other page with logic to steal goats
    return render_template(
      'other-userpage.html',
      username=username,
      logged_in=True,
      goat_imgs=current_app.config['goat_imgs']
    )

  # visiting a user's page when not logged in
  return render_template(
    'non-logged-in-userpage.html',
    username=username,
    logged_in=False,
    goat_imgs=current_app.config['goat_imgs']
  )
