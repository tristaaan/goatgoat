import uuid
import datetime

import jwt
import time
import graphene

from functools import wraps
from graphql import GraphQLError
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from flask_graphql_auth import (
    AuthInfoField,
    GraphQLAuth,
    get_jwt_identity,
    create_access_token,
    create_refresh_token,
    query_header_jwt_required,
    mutation_jwt_refresh_token_required,
    mutation_jwt_required
)
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from .models import db, User, Goat, Transaction
from config import SECRET_KEY

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
    user_by_id = graphene.Field(UserObject, id=graphene.Int())
    user_by_name = graphene.Field(UserObject, name=graphene.String())
    user_by_email = graphene.Field(UserObject, email=graphene.String())

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

    all_goats = SQLAlchemyConnectionField(GoatObject)
    goats_by_username = graphene.List(GoatObject, name=graphene.String())
    def resolve_goats_by_username(self, info, **kwargs):
        name = kwargs.get('name')
        user = User.query.filter_by(name=name).first()
        return Goat.query.filter(
            Goat.owner == user.id
        ).all()

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
        confirm_password = graphene.String(required=True)

    user = graphene.Field(UserObject)

    def mutate(self, info, email, username, password, confirm_password):
        if password != confirm_password:
            raise GraphQLError('Passwords do not match')

        if db.session.query(User).filter(User.name == username).first():
            raise GraphQLError('Username is already in use')

        if db.session.query(User).filter(User.email == email).first():
            raise GraphQLError('An account with this email already exists')

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(email, username, hashed_password)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise GraphQLError(e.message)

        for i in range(5):
            goat = Goat(new_user.id)
            db.session.add(goat)
        db.session.commit()
        return CreateUser(user=new_user)


class LoginUser(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        password = graphene.String()

    access_token = graphene.String()
    refresh_token = graphene.String()

    def mutate(self, info, name, password):
        invalid_message = 'Invalid username or password'
        user = User.query.filter_by(name=name).first()
        if user is None:
            raise GraphQLError(invalid_message)

        if check_password_hash(user.pw, password):
            # expires in 5 days
            # ideally a refreshToken is issued
            claims = {'exp': int(time.time()) + (60 * 60 * 24 * 5)}
            return LoginUser(
                access_token = create_access_token(name, claims)
            )

        raise GraphQLError(invalid_message)


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


class TakeGoat(graphene.Mutation):
    class Arguments:
        from_user = graphene.Int()
        to_user = graphene.Int()
        goat_id = graphene.Int()

    transaction = graphene.Field(TransactionObject)
    goat = graphene.Field(GoatObject)

    def mutate(self, info, from_user, to_user, goat_id):
        # create transaction
        new_transaction = Transaction(from_user, to_user, goat_id)
        db.session.add(new_transaction)

        # update goat
        db.session.update(Goat).where(Goat.id == goat_id).values(owner=to_user)

        # commit
        db.session.commit()
        return TakeGoat(transaction=new_transaction)

class GiveGoat(TakeGoat):
    def mutate(self, info, from_user, to_user, goat_id):
        # create transaction
        new_transaction = Transaction(from_user, to_user, goat_id)
        db.session.add(new_transaction)

        # update goat
        db.session.update(Goat).where(Goat.id == goat_id).values(owner=to_user)

        # commit
        db.session.commit()
        return GiveGoat(transaction=new_transaction)

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    login_user = LoginUser.Field()
    create_goats = CreateGoats.Field()

    take_goat = TakeGoat.Field()
    give_goat = GiveGoat.Field()

schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[UserObject, GoatObject, TransactionObject]
)
