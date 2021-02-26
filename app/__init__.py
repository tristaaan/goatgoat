from flask import Flask
from flask_migrate import Migrate
from flask_graphql import GraphQLView
from flask_graphql_auth import GraphQLAuth

from .models import db
from .views import views
from .gql_schema import schema

# initializing our app
app = Flask(__name__)
app.config.from_object('config')

# register views
app.register_blueprint(views)

# GraphQL route
app.add_url_rule(
    '/graphql-api',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True # for having the GraphiQL interface
    )
)
db.init_app(app)
GraphQLAuth(app)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

migrate = Migrate(app, db)
