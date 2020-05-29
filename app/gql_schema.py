import graphene
from . import models
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField

# Schema Objects
class TransactionObject(SQLAlchemyObjectType):
    class Meta:
        model = models.Transaction
        interfaces = (graphene.relay.Node, )

class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = models.User
        interfaces = (graphene.relay.Node, )

class GoatObject(SQLAlchemyObjectType):
    class Meta:
        model = models.Goat
        interfaces = (graphene.relay.Node, )

class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_goats = SQLAlchemyConnectionField(GoatObject)
    all_transactions = SQLAlchemyConnectionField(TransactionObject)
    all_users = SQLAlchemyConnectionField(UserObject)

schema = graphene.Schema(query=Query)
