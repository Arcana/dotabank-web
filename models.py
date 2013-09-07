from app import db
from flask.ext.login import current_user


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    enabled = db.Column(db.Boolean, default=True)

    replay_ratings = db.relationship('ReplayRating', backref='user', lazy='dynamic')

    def __init__(self, _id=None, name=None, enabled=True):
        self.id = _id
        self.name = name
        self.enabled = enabled

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

    ratings = db.relationship('ReplayRating', backref='replay', lazy='dynamic')

    def __init__(self, _id=None, url=None, state="UNKNOWN", parse_state="WAITING_GC"):
        self.id = _id
        self.url = url
        self.state = state
        self.parse_state = parse_state

    def __repr__(self):
        return "<Replay {}>".format(self.id)

    def user_rating(self):
        if current_user.is_authenticated():
            return next((rating for rating in self.ratings if rating.user_id == int(current_user.id)), None)
        else:
            return None


class ReplayRating(db.Model):
    __tablename__ = "replay_ratings"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    positive = db.Column(db.Boolean)

    def __init__(self, replay_id=None, user_id=None, positive=None):
        self.replay_id = replay_id
        self.user_id = user_id
        self.positive = positive

    def __repr__(self):
        return "<Rating {}/{}>".format(self.replay_id, self.user_id)
