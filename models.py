from app import db
from flask.ext.login import current_user, AnonymousUserMixin
import datetime


class AnonymousUser(AnonymousUserMixin):

    def is_admin(self):
        return False


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    first_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    admin = db.Column(db.Boolean, default=False)

    replay_ratings = db.relationship('ReplayRating', backref='user', lazy='select', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='user', lazy='select', cascade="all, delete-orphan")

    def __init__(self, _id=None, name=None, enabled=True, first_seen=datetime.datetime.utcnow(), last_seen=datetime.datetime.utcnow()):
        self.id = _id
        self.name = name
        self.enabled = enabled
        self.first_seen = first_seen
        self.last_seen = last_seen

    def __repr__(self):
        return self.name

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return self.enabled

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def is_admin(self):
        return self.admin

    def update_last_seen(self):
        # Called every page load for current_user
        self.last_seen = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()


class Replay(db.Model):
    __tablename__ = "replays"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(80))
    state = db.Column(db.Enum(
        "WAITING_GC",
        "WAITING_DOWNLOAD",
        "DOWNLOAD_IN_PROGRESS",
        "WAITING_PARSE",
        "PARSE_IN_PROGRESS",
        "PARSED",
        "GC_ERROR",
        "PARSE_ERROR"
    ), default="WAITING_GC")
    replay_state = db.Column(db.Enum(
        "REPLAY_AVAILABLE",
        "REPLAY_NOT_RECORDED",
        "REPLAY_EXPIRED",
        "UNKNOWN"
    ), default="UNKNOWN")

    ratings = db.relationship('ReplayRating', backref='replay', lazy='joined', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='favourite', lazy='joined', cascade="all, delete-orphan")

    def __init__(self, _id=None, url="", replay_state="UNKNOWN", state="WAITING_GC"):
        self.id = _id
        self.url = url
        self.replay_state = replay_state
        self.state = state

    def __repr__(self):
        return "<Replay {}>".format(self.id)

    def user_rating(self):
        if current_user.is_authenticated():
            return next((rating for rating in self.ratings if rating.user_id == current_user.id), None)
        else:
            return None

    def user_favourite(self):
        if current_user.is_authenticated():
            return next((favourite for favourite in self.favourites if favourite.user_id == current_user.id), False)
        else:
            return False


class ReplayRating(db.Model):
    __tablename__ = "replay_ratings"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    positive = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, replay_id=None, user_id=None, positive=None):
        self.replay_id = replay_id
        self.user_id = user_id
        self.positive = positive

    def __repr__(self):
        return "<Rating {}/{}>".format(self.replay_id, self.user_id)


class ReplayFavourite(db.Model):
    __tablename__ = "replay_favs"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    def __init__(self, replay_id=None, user_id=None):
        self.replay_id = replay_id
        self.user_id = user_id

    def __repr__(self):
        return "<Favourite {}/{}>".format(self.replay_id, self.user_id)


class GCWorker(db.Model):
    __tablename__ = "gc_workers"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.BLOB, nullable=False)
    display_name = db.Column(db.String(32), nullable=False)
    auth_code = db.Column(db.String(32))
    sentry = db.Column(db.BLOB)

    jobs = db.relationship('GCJob', backref='worker', lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, username=None, password=None, display_name=None, auth_code=None):
        self.username = username,
        self.password = password,
        self.display_name = display_name
        self.auth_code = auth_code

    def __repr__(self):
        return "<GCWorker {}>".format(self.id)


class GCJob(db.Model):
    __tablename__ = "gc_jobs"
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("gc_workers.id", ondelete="CASCADE"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<GCJob {}>".format(self.id)
