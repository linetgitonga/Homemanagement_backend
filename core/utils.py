import hashlib
from django.db import transaction

def compute_hash(data):
    return hashlib.sha256(str(data).encode()).hexdigest()