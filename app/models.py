from app import cache, dotabank_bucket, db
from app.replays.models import Replay, ReplayDownload
from app.users.models import User
from datetime import datetime, timedelta
import logging
import traceback

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


class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)  # auto incrementing
    logger = db.Column(db.String(64))  # the name of the logger. (e.g. myapp.views)
    level = db.Column(db.String(16))  # info, debug, or error?
    trace = db.Column(db.Text)  # the full traceback printout
    msg = db.Column(db.Text)  # any custom log you may have included
    extra = db.Column(db.Text)  # Any extra data given
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # the current timestamp
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, logger=None, level=None, trace=None, msg=None, extra=None):
        self.logger = logger
        self.level = level
        self.trace = trace
        self.msg = msg
        self.extra = extra

    def __unicode__(self):
        return self.__repr__()

    def __repr__(self):
        return "<Log: %s - %s>" % (self.created_at.strftime('%m/%d/%Y-%H:%M:%S'), self.msg[:50])

    def resolve(self, user_id):
        """ Mark this entry as resolved / at least acknowledge it's been seen. """
        self.resolved_by_user_id = user_id
        self.resolved_at = datetime.utcnow()

    @property
    def resolved(self):
        return self.resolved_by_user_id is not None

