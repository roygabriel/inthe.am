from contextlib import contextmanager
import time

import redis

from django.conf import settings


class LockTimeout(Exception):
    pass


def get_lock_redis():
    return redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB
    )


def get_lock_name_for_store(store):
    return store.user.username + ".lock"


@contextmanager
def redis_lock(
    name,
    wait_timeout=10,
    lock_timeout=settings.LOCKFILE_TIMEOUT_SECONDS
):
    client = get_lock_redis()
    started = time.time()
    wait_expiry = started + wait_timeout

    while(started < wait_expiry):
        lock_expiry = time.time() + lock_timeout + 1
        result = client.setnx(name, str(lock_expiry))
        if result:
            # Got the lock!
            yield
            # Make sure that this operation didn't take longer than
            # a lock timeout -- if it did, don't delete the key, it might
            # be somebody elses!
            if lock_expiry > time.time():
                client.delete(name)
            return

        # Didn't get the lock!
        original_timestamp = client.get(name)
        if float(original_timestamp) > time.time():
            # The timestamp isn't yet expired, let's wait a second
            # and try again.
            time.sleep(1)
            continue

        getset_timestamp = client.getset(name, str(lock_expiry))
        if getset_timestamp == original_timestamp:
            # We got the lock!
            yield
            # Make sure that this operation didn't take longer than
            # a lock timeout -- if it did, don't delete the key, it might
            # be somebody elses!
            if lock_expiry > time.time():
                client.delete(name)
            return
        else:
            # Somebody else got it first, let's wait a second
            # and try again.
            time.sleep(1)
            continue

    raise LockTimeout("Unable to acquire lock %s" % name)
