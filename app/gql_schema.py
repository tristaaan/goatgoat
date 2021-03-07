import uuid
import datetime
import string

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

# Schema Objects
class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node, )
        exclude_fields=('pw', 'pwResetToken', 'pwResetExpires')

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
    user_by_id = graphene.Field(UserObject, user_id=graphene.Int())
    user_by_name = graphene.Field(UserObject, name=graphene.String())
    user_by_email = graphene.Field(UserObject, email=graphene.String())

    def resolve_user_by_id(self, info, **kwargs):
        user_id = kwargs.get('user_id')
        return User.query.filter_by(user_id=user_id).first()

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
        return Goat.query.filter(Goat.owner_id == _id).all()

    # TRANSACTIONs
    all_transactions = SQLAlchemyConnectionField(TransactionObject)
    transactions_from = graphene.List(TransactionObject, user_id=graphene.Int())
    def resolve_transactions_from(self, info, **kwargs):
        user_id = kwargs.get('user_id')
        return Transaction.query.filter_by(from_user_id=user_id) \
            .order_by(Transaction.timestamp) \
            .limit(10)

    transactions_to = graphene.List(TransactionObject, user_id=graphene.Int())
    def resolve_transactions_to(self, info, **kwargs):
        user_id = kwargs.get('user_id')
        return Transaction.query.get(to_user_id=user_id)

    transactions_for_goat = graphene.List(TransactionObject, goat_id=graphene.Int())
    def resolve_transactions_for_goat(self, info, **kwargs):
        goat_id = kwargs['goat_id']
        return Transaction.query.filter_by(goat_id=goat_id).all()


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

        if len(set.difference(set(username.lower()), set(string.ascii_lowercase+string.digits))) > 0:
            raise GraphQLError('Username can only have letters and numbers')

        if username.lower() in ['settings', 'login', 'logout', 'forgot', 'reset', 'signup']:
            raise GraphQLError('Invalid username')

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
            goat = Goat(new_user.user_id)
            db.session.add(goat)
        db.session.commit()
        return CreateUser(user=new_user)


class LoginUser(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        password = graphene.String()

    access_token = graphene.String()
    # refresh_token = graphene.String()

    def mutate(self, info, name, password):
        invalid_message = 'Invalid username or password'
        user = User.query.filter_by(name=name).first()
        if user is None:
            raise GraphQLError(invalid_message)

        if check_password_hash(user.pw, password):
            return LoginUser(
                access_token = create_access_token(name)
            )

        raise GraphQLError(invalid_message)


class UpdateUserEmail(graphene.Mutation):
    class Arguments:
        token = graphene.String()
        new_email = graphene.String()

    new_email = graphene.String()

    @mutation_jwt_required
    def mutate(self, info, new_email):
        name = get_jwt_identity()
        if name is not None:
            user = User.query.filter_by(name=name).first()
            user.email = new_email
            try:
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise GraphQLError(e.message)
            return UpdateUserEmail(new_email=new_email)

        raise GraphQLError('invalid token')


class UpdateUserPassword(graphene.Mutation):
    class Arguments:
        token = graphene.String()
        new_password = graphene.String()
        confirm_password = graphene.String()

    success = graphene.Boolean()

    @mutation_jwt_required
    def mutate(self, info, new_password, confirm_password):
        if new_password != confirm_password:
            raise GraphQLError('Passwords do not match')

        name = get_jwt_identity()
        if name is not None:
            hashed_password = generate_password_hash(new_password, method='sha256')
            user = User.query.filter_by(name=name).first()
            user.pw = hashed_password
            try:
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise GraphQLError(e.message)
            return UpdateUserPassword(success=True)

        raise GraphQLError('invalid token')


class UpdateUserGoat(graphene.Mutation):
    class Arguments:
        token = graphene.String()
        new_goat = graphene.Int()

    success = graphene.Boolean()

    @mutation_jwt_required
    def mutate(self, info, new_goat):
        name = get_jwt_identity()
        if name is not None:
            user = User.query.filter_by(name=name).first()
            user.goatvatar = new_goat
            try:
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise GraphQLError(e.message)
            return UpdateUserGoat(success=True)

        raise GraphQLError('invalid token')


class CreateGoats(graphene.Mutation):
    class Arguments:
        count = graphene.String()
        owner_id = graphene.Int()

    goats = graphene.List(GoatObject)

    def mutate(self, info, count, owner_id):
        new_goats = []
        for i in range(count):
            new_goat = Goat(owner_id)
            db.session.add(new_goat)
            new_goats.push(GoatObject(new_goat))
        db.session.commit()
        return CreateGoats(goats=new_goats)


class TakeGoat(graphene.Mutation):
    class Arguments:
        token = graphene.String()
        from_user = graphene.Int()
        goat_id = graphene.Int()

    transaction = graphene.Field(TransactionObject)

    @mutation_jwt_required
    def mutate(self, info, from_user, goat_id):
        name = get_jwt_identity()
        goat = Goat.query.filter_by(goat_id=goat_id).first()
        to_user = User.query.filter_by(name=name).first()
        if to_user.user_id == from_user or to_user.user_id == goat.owner_id:
            raise GraphQLError('You cannot take your own goat')

        # create transaction
        new_transaction = Transaction(from_user, to_user.user_id, goat_id)
        db.session.add(new_transaction)

        # update goat
        goat.owner_id = to_user.user_id

        # commit
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise GraphQLError(e.message)
        return TakeGoat(transaction=new_transaction)


# class GiveGoat(TakeGoat):
#     def mutate(self, info, from_user, to_user, goat_id):
#         # create transaction
#         new_transaction = Transaction(from_user, to_user, goat_id)
#         db.session.add(new_transaction)

#         # update goat
#         db.session.update(Goat).where(Goat.id == goat_id).values(owner_id=to_user)

#         # commit
#         db.session.commit()
#         return GiveGoat(transaction=new_transaction)


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    login_user = LoginUser.Field()
    update_user_email = UpdateUserEmail.Field()
    update_user_password = UpdateUserPassword.Field()
    update_user_goat = UpdateUserGoat.Field()

    create_goats = CreateGoats.Field()
    take_goat = TakeGoat.Field()
    # give_goat = GiveGoat.Field()


schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[UserObject, GoatObject, TransactionObject]
)
