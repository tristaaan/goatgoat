import glob
import base64
from os import path

from flask import Flask
from flask_migrate import Migrate
from flask_graphql import GraphQLView
from flask_graphql_auth import GraphQLAuth
from celery import Celery

from .models import db


celery = Celery(__name__)
celery.config_from_object('celery_config')

migrate = None

def create_app():
  # initializing our app
  app = Flask(__name__)
  app.config.from_object('config')

  # register views
  from .views import views
  app.register_blueprint(views)

  # GraphQL init
  ## GraphQL route
  from .gql_schema import schema
  app.add_url_rule(
      '/graphql-api',
      view_func=GraphQLView.as_view(
          'graphql',
          schema=schema,
          graphiql=app.config['DEBUG'] # for having the GraphiQL interface
      )
  )
  db.init_app(app)
  GraphQLAuth(app)

  # Flask request setup
  @app.before_first_request
  def before_first_request():
    fpath = path.join(
      path.abspath(path.dirname(__file__)),
      'static',
      'img/goatvatar/*.png'
    )
    files = sorted(glob.glob(fpath))
    base64_images = []
    for f in files:
      with open(f, 'rb') as img:
        base64_images.append(
          base64.b64encode(img.read()).decode('utf8')
        )
    app.config['goat_imgs'] = base64_images

  @app.teardown_appcontext
  def shutdown_session(exception=None):
      db.session.remove()

  migrate = Migrate(app, db)

  return app


