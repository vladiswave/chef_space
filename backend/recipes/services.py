import base64
import hashlib
import uuid

from .constants import HASH_GENERATION_ATTEMPTS, SHORT_HASH_LENGTH


def generate_short_hash(model):
    for _ in range(HASH_GENERATION_ATTEMPTS):
        full_uuid = uuid.uuid4().hex
        hash_bytes = hashlib.sha256(full_uuid.encode()).digest()
        encoded = base64.urlsafe_b64encode(hash_bytes).decode()
        short_hash = encoded[:SHORT_HASH_LENGTH]
        if not model.objects.filter(short_hash=short_hash).exists():
            return short_hash
    raise RuntimeError('Не удалось сгенерировать уникальный короткий хеш')
