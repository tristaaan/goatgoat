from enum import Enum


class TransactionStatus(Enum):
  APPROVED = 'approved'
  DENIED = 'denied'
  PENDING = 'pending'
