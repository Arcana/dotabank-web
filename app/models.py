from app import cache, dotabank_bucket
from app.replays.models import Replay, ReplayDownload
from app.users.models import User
from datetime import datetime, timedelta


class Stats:
    def __init__(self):
        pass

    @staticmethod
    @cache.memoize(timeout=60*60)
    def replays_count(hours=None):
        if hours:
            _time_ago = datetime.utcnow() - timedelta(hours=hours)
            return Replay.query.filter(Replay.added_to_site_time >= _time_ago).count()
        else:
            return Replay.query.count()

    @staticmethod
    @cache.memoize(timeout=60*60)
    def archived_count(hours=None):
        if hours:
            _time_ago = datetime.utcnow() - timedelta(hours=hours)
            return Replay.query.filter(Replay.local_uri != None,
                                            Replay.added_to_site_time >= _time_ago).count()  # Have to use != instead of 'is not' here, because sqlalchemy.
        else:
            return Replay.query.filter(Replay.local_uri != None).count()  # Have to use != instead of 'is not' here, because sqlalchemy.

    @staticmethod
    @cache.memoize(timeout=60*60)
    def downloads_count(hours=None):
        if hours:
            _time_ago = datetime.utcnow() - timedelta(hours=hours)
            return ReplayDownload.query.filter(ReplayDownload.created_at >= _time_ago).count()
        else:
            return ReplayDownload.query.count()

    @staticmethod
    @cache.memoize(timeout=60*60)
    def users_count(hours=None):
        if hours:
            _time_ago = datetime.utcnow() - timedelta(hours=hours)
            return User.query.filter(User.first_seen >= _time_ago).count()
        else:
            return User.query.count()

    @staticmethod
    @cache.memoize(timeout=60*60)
    def bucket_size():
        total_bytes = 0
        for key in dotabank_bucket:
            total_bytes += key.size

        return total_bytes


