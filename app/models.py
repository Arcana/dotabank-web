from app import mem_cache, dotabank_bucket, db, steam
from app.replays.models import Replay, ReplayDownload
from app.users.models import User
from datetime import datetime, timedelta


class Stats:
    """ Model used for public stats visible on Dotabank home page """
    def __init__(self):
        pass

    @staticmethod
    @mem_cache.memoize(timeout=60 * 60)
    def replays_count(hours=None):
        """ Counts how many replays have been added to the database since `hours` ago, or all-time if `hours` is None. """
        if hours:
            _time_ago = datetime.utcnow() - timedelta(hours=hours)
            return Replay.query.filter(Replay.added_to_site_time >= _time_ago).count()
        else:
            return Replay.query.count()

    @staticmethod
    @mem_cache.memoize(timeout=60 * 60)
    def archived_count(hours=None):
        """ Counts how many replays have been archived since `hours` ago, or all-time if `hours` is None. """
        if hours:
            _time_ago = datetime.utcnow() - timedelta(hours=hours)
            return Replay.query.filter(Replay.local_uri != None,
                                            Replay.added_to_site_time >= _time_ago).count()  # Have to use != instead of 'is not' here, because sqlalchemy.
        else:
            return Replay.query.filter(Replay.local_uri != None).count()  # Have to use != instead of 'is not' here, because sqlalchemy.

    @staticmethod
    @mem_cache.memoize(timeout=60 * 60)
    def downloads_count(hours=None):
        """ Counts how many times users have initiated a download since `hours` ago, or all-time if `hours` is None. """
        if hours:
            _time_ago = datetime.utcnow() - timedelta(hours=hours)
            return ReplayDownload.query.filter(ReplayDownload.created_at >= _time_ago).count()
        else:
            return ReplayDownload.query.count()

    @staticmethod
    @mem_cache.memoize(timeout=60 * 60)
    def users_count(hours=None):
        """ Counts how many users have registered (first login) since `hours` ago, or all-time if `hours` is None. """
        if hours:
            _time_ago = datetime.utcnow() - timedelta(hours=hours)
            return User.query.filter(User.first_seen >= _time_ago).count()
        else:
            return User.query.count()

    @staticmethod
    @mem_cache.memoize(timeout=60 * 60)
    def bucket_size():
        """ Sums up and returns how much space we're taking up on our dotabank S3 bucket. """
        total_bytes = 0
        for key in dotabank_bucket:
            total_bytes += key.size

        return total_bytes


class Log(db.Model):
    """ Model used for logging to database. """
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

    # Set default order by
    __mapper_args__ = {
        "order_by": [db.asc(created_at)]
    }

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
        """ Mark this log as resolved / at least acknowledge it's been seen. """
        if not self.resolved:
            self.resolved_by_user_id = user_id
            self.resolved_at = datetime.utcnow()

    @property
    def resolved(self):
        """ Returns whether this log has been resolved or not. """
        return self.resolved_by_user_id is not None


class UGCFile(db.Model):
    __tablename__ = "ugcfiles"

    id = db.Column(db.BigInteger, primary_key=True)
    filename = db.Column(db.String(80))
    size = db.Column(db.Integer)
    url = db.Column(db.String(140))

    def __init__(self, _id, filename=None, size=None, url=None):
        self.id = _id
        self.filename = filename
        self.size = size
        self.url = url

        if filename is None or size is None or url is None:
            self._populate_from_webapi()

    def _populate_from_webapi(self):
        try:
            file_info = steam.remote_storage.ugc_file(570, self.id)
            self.filename = file_info.filename
            self.size = file_info.size
            self.url = file_info.url
        except steam.api.SteamError:
            pass
