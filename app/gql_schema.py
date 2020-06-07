import graphene
from .models import db, User, Goat, Transaction
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField


# Schema Objects
class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node, )

class GoatObject(SQLAlchemyObjectType):
    class Meta:
        model = Goat
        interfaces = (graphene.relay.Node, )

class TransactionObject(SQLAlchemyObjectType):
    class Meta:
        model = Transaction
        interfaces = (graphene.relay.Node, )

# TODO:
# get transactions by user
# get goats by user

class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()

    # USERs
    all_users = SQLAlchemyConnectionField(UserObject)
    user_by_id = graphene.Field(lambda: UserObject, id=graphene.Int())
    user_by_name = graphene.Field(lambda: UserObject, name=graphene.String())
    user_by_email = graphene.Field(lambda: UserObject, email=graphene.String())
    def resolve_user_by_id(self, info, **kwargs):
        _id = kwargs.get('id')
        return User.query.filter_by(id=_id).first()

    def resolve_user_by_name(self, info, **kwargs):
        name = kwargs.get('name')
        return User.query.filter_by(name=name).first()

    def resolve_user_by_email(self, info, **kwargs):
        email = kwargs.get('email')
        return User.query.filter_by(email=email).first()

    # GOATs
    all_goats = SQLAlchemyConnectionField(GoatObject)
    goats_by_owner_id = graphene.List(GoatObject, id=graphene.Int())
    def resolve_goats_by_owner_id(self, info, **kwargs):
        _id = kwargs.get('id')
        return Goat.query.filter(Goat.owner == _id).all()

    # TRANSACTIONs
    all_transactions = SQLAlchemyConnectionField(TransactionObject)
    transactions_from = graphene.List(TransactionObject, from_user=graphene.Int())
    transactions_to = graphene.List(TransactionObject, to_user=graphene.Int())
    def resolve_transactions_from(self, info, **kwargs):
        from_user = kwargs.get('from_user')
        return Transaction.query.get(from_user=from_user)

    def resolve_transactions_to(self, info, **kwargs):
        to_user = kwargs.get('to_user')
        return Transaction.query.get(to_user=to_user)

# Mutations
class CreateUser(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserObject)

    def mutate(self, info, email, username, password):
        new_user = User(email, username, password)
        db.session.add(new_user)
        db.session.commit()
        for i in range(5):
            goat = Goat(new_user.id)
            db.session.add(goat)
        db.session.commit()
        return CreateUser(user=new_user)


class CreateGoats(graphene.Mutation):
    class Arguments:
        count = graphene.String()
        owner = graphene.Int()

    goats = graphene.List(GoatObject)

    def mutate(self, info, count, owner):
        new_goats = []
        for i in range(count):
            new_goat = Goat(owner)
            db.session.add(new_goat)
            new_goats.push(GoatObject(new_goat))
        db.session.commit()
        return CreateGoats(goats=new_goats)


class CreateTransaction(graphene.Mutation):
    class Arguments:
        from_user = graphene.String()
        to_user = graphene.String()
        goat = graphene.String()

    transaction = graphene.Field(TransactionObject)

    def mutate(self, info, from_user, to_user, goat):
        new_transaction = Transaction(from_user, to_user, goat)
        db.session.add(new_transaction)
        db.session.commit()
        return CreateTransaction(transaction=new_transaction)

# TODO:
# take goat mutation
# give goat mutation

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_goats = CreateGoats.Field()
    create_transaction = CreateTransaction.Field()

schema = graphene.Schema(query=Query, mutation=Mutation, types=[UserObject, GoatObject, TransactionObject])
