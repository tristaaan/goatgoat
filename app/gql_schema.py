import uuid
import string
from datetime import datetime, timedelta

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

from .enums import TransactionStatus
from .models import db, User, Goat, Transaction, Vote
from .tasks import transaction_completion

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


class VoteObject(SQLAlchemyObjectType):
    class Meta:
        model = Vote
        interfaces = (graphene.relay.Node, )


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()

    # USERs
    all_users = SQLAlchemyConnectionField(UserObject.connection)
    user_by_id = graphene.Field(UserObject, user_id=graphene.Int())
    user_by_name = graphene.Field(UserObject, name=graphene.String())
    user_by_email = graphene.Field(UserObject, email=graphene.String())

    def resolve_user_by_id(self, info, **kwargs):
        user_id = kwargs.get('user_id')
        return User.query.filter_by(user_id=user_id).first()

    def resolve_user_by_name(self, info, **kwargs):
        name = kwargs.get('name')
        return User.query.filter_by(name=name.lower()).first()

    def resolve_user_by_email(self, info, **kwargs):
        email = kwargs.get('email')
        return User.query.filter_by(email=email).first()

    # GOATs
    all_goats = SQLAlchemyConnectionField(GoatObject.connection)
    goats_by_owner_id = graphene.List(GoatObject, id=graphene.Int())
    def resolve_goats_by_owner_id(self, info, **kwargs):
        _id = kwargs.get('id')
        return Goat.query.filter(Goat.owner_id == _id).all()

    # TRANSACTIONs
    all_transactions = SQLAlchemyConnectionField(TransactionObject.connection)
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

    # VOTEs
    votes_for_transaction = graphene.List(VoteObject, transaction_id=graphene.Int())
    def resolve_votes_for_transaction(self, info, **kwargs):
        transaction_id = kwargs.get('transaction_id')
        return Vote.query.filter_by(transaction_id=transaction_id).all()


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

        username = username.lower()
        if len(set.difference(set(username), set(string.ascii_lowercase+string.digits))) > 0:
            raise GraphQLError('Username can only have letters and numbers')

        if username in ['settings', 'login', 'logout', 'forgot', 'reset', 'signup', 'ledger']:
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
        name = name.lower()
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
            user = User.query.filter_by(name=name.lower()).first()
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
            user = User.query.filter_by(name=name.lower()).first()
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
            user = User.query.filter_by(name=name.lower()).first()
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
        to_user = User.query.filter_by(name=name.lower()).first()
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


class StartTransaction(graphene.Mutation):
    class Arguments:
        token = graphene.String()
        from_user = graphene.Int()
        goat_id = graphene.Int()

    transaction = graphene.Field(TransactionObject)

    @mutation_jwt_required
    def mutate(self, info, from_user, goat_id):
        name = get_jwt_identity()
        goat = Goat.query.filter_by(goat_id=goat_id).first()
        to_user = User.query.filter_by(name=name.lower()).first()
        # user cannot take their own goat
        if to_user.user_id == from_user or to_user.user_id == goat.owner_id:
            raise GraphQLError('You cannot take your own goat')

        existing_transactions = Transaction.query.filter_by(
            goat_id=goat.goat_id, status=TransactionStatus.PENDING.value).all()
        if len(existing_transactions) > 0:
            raise GraphQLError('There already exists a transaction for this goat')

        # create transaction
        new_transaction = Transaction(from_user, to_user.user_id, goat_id)
        db.session.add(new_transaction)

        # commit
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise GraphQLError(e.message)

        # enqueue task
        tid = new_transaction.transaction_id
        eta = datetime.utcnow() + timedelta(seconds=30)
        transaction_completion.apply_async(kwargs={'transaction_id': tid}, eta=eta)

        # return goat
        return StartTransaction(transaction=new_transaction)


class CreateVote(graphene.Mutation):
    class Arguments:
        token = graphene.String()
        transaction_id = graphene.Int()
        value = graphene.Int()

    status = graphene.Boolean()

    @mutation_jwt_required
    def mutate(self, info, transaction_id, value):
        name = get_jwt_identity()
        user = User.query.filter_by(name=name).first()
        # assert transaction is pending
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
        if transaction.status != TransactionStatus.PENDING:
            return GraphQLError('Cannot vote on resolved transaction')

        # assert user has not double voted
        old_votes = Vote.query.filter_by(transaction_id=transaction_id, voter_id=user_id).all()
        if len(old_votes) > 0:
            return GraphQLError('You have already voted on this transaction')

        # assert user is not the to_user in transaction
        if user.user_id == transaction.to_user_id:
            return GraphQLError('You cannot vote on a transaction that you initiated')

        new_vote = Vote(transaction_id, user.user_id, value)
        db.session.add(new_vote)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise GraphQLError(e.message)
        return CreateVote(status=True)


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    login_user = LoginUser.Field()
    update_user_email = UpdateUserEmail.Field()
    update_user_password = UpdateUserPassword.Field()
    update_user_goat = UpdateUserGoat.Field()

    create_goats = CreateGoats.Field()
    take_goat = TakeGoat.Field()
    # give_goat = GiveGoat.Field()

    start_transaction = StartTransaction.Field()
    create_vote = CreateVote.Field()

schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[UserObject, GoatObject, TransactionObject]
)
