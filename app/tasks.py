from functools import reduce
import datetime
import logging

from celery.utils.log import get_task_logger

from app import celery
from .enums import TransactionStatus
from .models import db, User, Goat, Transaction, Vote

logger = get_task_logger(__name__)

# tasks
@celery.task()
def transaction_completion(transaction_id):
    logger.info('tallying votes')
    # tally votes
    votes = Vote.query.filter_by(transaction_id=transaction_id).all()
    result = reduce(lambda prev,cur: prev + cur.value, votes, 0)

    if result <= 0:
        next_status = TransactionStatus.DENIED
    else:
        next_status = TransactionStatus.APPROVED
    logger.info(f'vote result: "{next_status.value}"')

    # mark transaction as resolved
    logger.info(f'updating transaction "{transaction_id}"')
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
    transaction.status = next_status.value
    transaction.resolved = datetime.datetime.now()

    # transfer goat if vote successful
    if next_status == TransactionStatus.APPROVED:
        logger.info(f'transfering goat: "{transaction.goat_id}"')
        goat = Goat.query.filter_by(goat_id=transaction.goat_id)
        goat.owner_id = transaction.to_user_id

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f'Error with transaction completion: {e}')

    logger.info('complete')
