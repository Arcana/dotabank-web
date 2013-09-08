from app import db
from flask.ext.login import current_user


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    replay_ratings = db.relationship('ReplayRating', backref='user', lazy='select', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='user', lazy='select', cascade="all, delete-orphan")

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

    ratings = db.relationship('ReplayRating', backref='replay', lazy='joined', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='favourite', lazy='joined', cascade="all, delete-orphan")

    def __init__(self, _id=None, url="", state="UNKNOWN", parse_state="WAITING_GC"):
        self.id = _id
        self.url = url
        self.state = state
        self.parse_state = parse_state

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
